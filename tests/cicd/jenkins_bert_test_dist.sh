#!/bin/bash

# set vars
MODEL_NAME="bert"
DATA_PATH="/home/vmagent/app/dataset/SQuAD"
CONF_FILE="tests/cicd/conf/e2eaiok_defaults_bert_dist_example.conf"

# enable oneAPI
source /opt/intel/oneapi/setvars.sh --ccl-configuration=cpu_icc --force

# create ci log dir
hashstr_id=$(date +%Y-%m-%d)_$(echo $RANDOM | md5sum | head -c 8)
tmp_dir="/home/vmagent/app/cicd_logs/e2eaiok_cicd_"$MODEL_NAME"_"$hashstr_id
mkdir -p $tmp_dir

# config passwordless ssh
service ssh start
ssh-keyscan -p 12344 -H 10.1.2.208 >> /root/.ssh/known_hosts
ssh-keyscan -p 12344 -H 10.1.2.213 >> /root/.ssh/known_hosts

cd /home/vmagent/app/e2eaiok/modelzoo/bert && printf '10.1.2.213:enp134s0f1\n10.1.2.208:enp134s0f1\n' > hosts
set -e
# lauch e2eaiok wnd
cd /home/vmagent/app/e2eaiok
if [ $USE_SIGOPT == 1 ]; then
  SIGOPT_API_TOKEN=$SIGOPT_API_TOKEN python run_e2eaiok.py --data_path $DATA_PATH --model_name $MODEL_NAME --conf $CONF_FILE --custom_result_path $tmp_dir 2>&1 | tee $tmp_dir/e2eaiok_cicd.log
else
  python run_e2eaiok.py --data_path $DATA_PATH --model_name $MODEL_NAME --conf $CONF_FILE --no_sigopt --custom_result_path $tmp_dir 2>&1 | tee $tmp_dir/e2eaiok_cicd.log
fi

# test
LANG=C SIGOPT_API_TOKEN=$SIGOPT_API_TOKEN MODEL_NAME=$MODEL_NAME DATA_PATH=$DATA_PATH CUSTOM_RESULT_PATH=$tmp_dir tests/cicd/bats/bin/bats tests/cicd/test_result_exist.bats
LANG=C SIGOPT_API_TOKEN=$SIGOPT_API_TOKEN MODEL_NAME=$MODEL_NAME DATA_PATH=$DATA_PATH CUSTOM_RESULT_PATH=$tmp_dir tests/cicd/bats/bin/bats tests/cicd/test_model_reload.bats