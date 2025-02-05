"""
 Copyright 2024 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

from pyrecdp.core.import_utils import check_availability_and_install, list_requirements

import os, pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
deps_require = list_requirements(os.path.join(cur_path, "requirements.txt"))
for pkg in deps_require:
    check_availability_and_install(pkg, verbose=0)

from pyrecdp.autofe.FeatureProfiler import *
from pyrecdp.autofe.FeatureWrangler import *
from pyrecdp.autofe.RelationalBuilder import *
from pyrecdp.autofe.FeatureEstimator import *
from pyrecdp.autofe.TabularPipeline import *
from pyrecdp.autofe.AutoFE import *