from .base import BaseLLMOperation, LLMOPERATORS
from ray.data import Dataset
from pyspark.sql import DataFrame
import os
from transformers import pipeline

from pyrecdp.primitives.llmutils.pii.pii_detection import scan_pii_text
from pyrecdp.primitives.llmutils.pii.pii_redaction import redact_pii_text, random_replacements

def prepare_func_pii_removal(model_root_path = "", debug_mode = True):
    replacements = random_replacements()
    _model_key = "bigcode/starpii"
    model_key = _model_key if model_root_path is None else os.path.join(model_root_path, _model_key)
    pipeline_inst = pipeline(model = model_key, task='token-classification', grouped_entities=True)

    def process_debug(sample):
        secrets = scan_pii_text(sample, pipeline_inst)
        text, is_modified = redact_pii_text(sample, secrets, replacements)
        return text, is_modified, str(secrets)
        
    def process(sample):
        secrets = scan_pii_text(sample, pipeline_inst)
        text, _ = redact_pii_text(sample, secrets, replacements)
        return text

    if debug_mode:
        return process_debug
    else:
        return process


class PIIRemoval(BaseLLMOperation):
    def __init__(self, text_key = 'text', inplace = True, model_root_path = "", debug_mode = False):
        settings = {'text_key': text_key, 'inplace': inplace, 'model_root_path': model_root_path, 'debug_mode': debug_mode}
        super().__init__(settings)
        self.text_key = text_key
        self.inplace = inplace
        self.model_root_path = model_root_path
        self.actual_func = None
        self.support_spark = True
        self.support_ray = True
        self.debug_mode = debug_mode
        
    def process_rayds(self, ds: Dataset) -> Dataset:
        if self.inplace:
            new_name = self.text_key
        else:
            new_name = 'pii_clean_text'
        if self.actual_func is None:
            self.actual_func = prepare_func_pii_removal(self.model_root_path, debug_mode=self.debug_mode)
        if self.debug_mode:
            def process_row(sample: dict, text_key, new_name, actual_func, *actual_func_args):
                sample[new_name], sample['is_modified_by_pii'], sample['secrets'] = actual_func(sample[text_key], *actual_func_args)
                return sample
            return ds.map(lambda x: process_row(x, self.text_key, new_name, self.actual_func))
        else:
            return ds.map(lambda x: self.process_row(x, self.text_key, new_name, self.actual_func))
    
    def process_spark(self, spark, spark_df: DataFrame) -> DataFrame:
        import pyspark.sql.functions as F
        from pyspark.sql import types as T
        if self.inplace:
            new_name = self.text_key
        else:
            new_name = 'pii_clean_text'
            
        if self.debug_mode:
            schema = T.StructType([
                T.StructField(new_name, T.StringType(), False),
                T.StructField('is_modified_by_pii', T.BooleanType(), False),
                T.StructField('secrets', T.StringType(), False)
            ])
            existing_cols = [col_name for col_name in spark_df.columns if col_name != new_name]
            pii_remove_udf = F.udf(prepare_func_pii_removal(self.model_root_path, debug_mode=self.debug_mode), schema)
            return spark_df.withColumn('pii_ret', pii_remove_udf(F.col(self.text_key))).select(*existing_cols, "pii_ret.*")
        else:
            pii_remove_udf = F.udf(prepare_func_pii_removal(self.model_root_path, debug_mode=self.debug_mode))
            return spark_df.withColumn(new_name, pii_remove_udf(F.col(self.text_key)))

LLMOPERATORS.register(PIIRemoval)