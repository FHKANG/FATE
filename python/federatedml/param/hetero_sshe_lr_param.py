#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import copy

from federatedml.param.base_param import BaseParam
from federatedml.param.cross_validation_param import CrossValidationParam
from federatedml.param.encrypt_param import EncryptParam
from federatedml.param.encrypted_mode_calculation_param import EncryptedModeCalculatorParam
from federatedml.param.init_model_param import InitParam
from federatedml.param.predict_param import PredictParam
from federatedml.param.stepwise_param import StepwiseParam
from federatedml.util import consts


class LogisticRegressionParam(BaseParam):
    """
    Parameters used for Logistic Regression both for Homo mode or Hetero mode.

    Parameters
    ----------
    penalty : str, 'L1', 'L2' or None. default: 'L2'
        Penalty method used in LR. Please note that, when using encrypted version in HomoLR,
        'L1' is not supported.

    tol : float, default: 1e-4
        The tolerance of convergence

    alpha : float, default: 1.0
        Regularization strength coefficient.

    optimizer : str, 'sgd', 'rmsprop', 'adam', 'nesterov_momentum_sgd', 'sqn' or 'adagrad', default: 'rmsprop'
        Optimize method, if 'sqn' has been set, sqn_param will take effect. Currently, 'sqn' support hetero mode only.

    batch_size : int, default: -1
        Batch size when updating model. -1 means use all data in a batch. i.e. Not to use mini-batch strategy.

    learning_rate : float, default: 0.01
        Learning rate

    max_iter : int, default: 100
        The maximum iteration for training.

    early_stop : str, 'diff', 'weight_diff' or 'abs', default: 'diff'
        Method used to judge converge or not.
            a)	diff： Use difference of loss between two iterations to judge whether converge.
            b)  weight_diff: Use difference between weights of two consecutive iterations
            c)	abs: Use the absolute value of loss to judge whether converge. i.e. if loss < eps, it is converged.

            Please note that for hetero-lr multi-host situation, this parameter support "weight_diff" only.

    decay: int or float, default: 1
        Decay rate for learning rate. learning rate will follow the following decay schedule.
        lr = lr0/(1+decay*t) if decay_sqrt is False. If decay_sqrt is True, lr = lr0 / sqrt(1+decay*t)
        where t is the iter number.

    decay_sqrt: Bool, default: True
        lr = lr0/(1+decay*t) if decay_sqrt is False, otherwise, lr = lr0 / sqrt(1+decay*t)

    encrypt_param: EncryptParam object, default: default EncryptParam object

    predict_param: PredictParam object, default: default PredictParam object

    cv_param: CrossValidationParam object, default: default CrossValidationParam object

    multi_class: str, 'ovr', default: 'ovr'
        If it is a multi_class task, indicate what strategy to use. Currently, support 'ovr' short for one_vs_rest only.

    validation_freqs: int, list, tuple, set, or None
        validation frequency during training.

    early_stopping_rounds: int, default: None
        Will stop training if one metric doesn’t improve in last early_stopping_round rounds

    metrics: list or None, default: None
        Indicate when executing evaluation during train process, which metrics will be used. If set as empty,
        default metrics for specific task type will be used. As for binary classification, default metrics are
        ['auc', 'ks']

    use_first_metric_only: bool, default: False
        Indicate whether use the first metric only for early stopping judgement.

    floating_point_precision: None or integer, if not None, use floating_point_precision-bit to speed up calculation,
                               e.g.: convert an x to round(x * 2**floating_point_precision) during Paillier operation, divide
                                      the result by 2**floating_point_precision in the end.

    review_strategy: str, "respectively", "all_review_in_guest", default: "respectively"
        "respectively": Means guest and host can review their own part of weights only.
        "all_review_in_guest": All the weights will be reviewed in guest only.
            This is use to protect the situation that, guest provided label only.
            Since if host obtain the model weights, it can use this model to steal
            label info of guest. However, to protect host's info, this function works
            only when guest provide no features. If there is any feature has been provided
            in Guest, this param is illegal.

    """

    def __init__(self, penalty='L2',
                 tol=1e-4, alpha=1.0, optimizer='rmsprop',
                 batch_size=-1, learning_rate=0.01, init_param=InitParam(),
                 max_iter=100, early_stop='diff', encrypt_param=EncryptParam(),
                 predict_param=PredictParam(),
                 decay=1, decay_sqrt=True,
                 multi_class='ovr', validation_freqs=None, early_stopping_rounds=None,
                 stepwise_param=StepwiseParam(), floating_point_precision=23,
                 metrics=None,
                 use_first_metric_only=False, use_mix_rand=False,
                 random_field=1 << 20, review_strategy="respectively"
                 ):
        super(LogisticRegressionParam, self).__init__()
        self.penalty = penalty
        self.tol = tol
        self.alpha = alpha
        self.optimizer = optimizer
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.init_param = copy.deepcopy(init_param)
        self.max_iter = max_iter
        self.early_stop = early_stop
        self.encrypt_param = encrypt_param
        self.predict_param = copy.deepcopy(predict_param)
        self.random_field = random_field
        self.decay = decay
        self.decay_sqrt = decay_sqrt
        self.multi_class = multi_class
        self.validation_freqs = validation_freqs
        self.stepwise_param = copy.deepcopy(stepwise_param)
        self.early_stopping_rounds = early_stopping_rounds
        self.metrics = metrics or []
        self.use_first_metric_only = use_first_metric_only
        self.floating_point_precision = floating_point_precision
        self.use_mix_rand = use_mix_rand
        self.review_strategy = review_strategy

    def check(self):
        descr = "logistic_param's"

        if self.penalty is None:
            pass
        elif type(self.penalty).__name__ != "str":
            raise ValueError(
                "logistic_param's penalty {} not supported, should be str type".format(self.penalty))
        else:
            self.penalty = self.penalty.upper()
            if self.penalty not in [consts.L1_PENALTY, consts.L2_PENALTY, 'NONE']:
                raise ValueError(
                    "logistic_param's penalty not supported, penalty should be 'L1', 'L2' or 'none'")

        if not isinstance(self.tol, (int, float)):
            raise ValueError(
                "logistic_param's tol {} not supported, should be float type".format(self.tol))

        if type(self.alpha).__name__ not in ["float", 'int']:
            raise ValueError(
                "logistic_param's alpha {} not supported, should be float or int type".format(self.alpha))

        if type(self.optimizer).__name__ != "str":
            raise ValueError(
                "logistic_param's optimizer {} not supported, should be str type".format(self.optimizer))
        else:
            self.optimizer = self.optimizer.lower()
            if self.optimizer not in ['sgd', 'rmsprop', 'adam', 'adagrad', 'nesterov_momentum_sgd', 'sqn']:
                raise ValueError(
                    "logistic_param's optimizer not supported, optimizer should be"
                    " 'sgd', 'rmsprop', 'adam', 'nesterov_momentum_sgd', 'sqn' or 'adagrad'")

        if self.batch_size != -1:
            if type(self.batch_size).__name__ not in ["int"] \
                    or self.batch_size < consts.MIN_BATCH_SIZE:
                raise ValueError(descr + " {} not supported, should be larger than {} or "
                                         "-1 represent for all data".format(self.batch_size, consts.MIN_BATCH_SIZE))

        if not isinstance(self.learning_rate, (float, int)):
            raise ValueError(
                "logistic_param's learning_rate {} not supported, should be float or int type".format(
                    self.learning_rate))

        self.init_param.check()

        if type(self.max_iter).__name__ != "int":
            raise ValueError(
                "logistic_param's max_iter {} not supported, should be int type".format(self.max_iter))
        elif self.max_iter <= 0:
            raise ValueError(
                "logistic_param's max_iter must be greater or equal to 1")

        if type(self.early_stop).__name__ != "str":
            raise ValueError(
                "logistic_param's early_stop {} not supported, should be str type".format(
                    self.early_stop))
        else:
            self.early_stop = self.early_stop.lower()
            if self.early_stop not in ['diff', 'abs', 'weight_diff']:
                raise ValueError(
                    "logistic_param's early_stop not supported, converge_func should be"
                    " 'diff', 'weight_diff' or 'abs'")

        self.encrypt_param.check()
        self.predict_param.check()
        if self.encrypt_param.method not in [consts.PAILLIER, None]:
            raise ValueError(
                "logistic_param's encrypted method support 'Paillier' or None only")

        if type(self.decay).__name__ not in ["int", 'float']:
            raise ValueError(
                "logistic_param's decay {} not supported, should be 'int' or 'float'".format(
                    self.decay))

        if type(self.decay_sqrt).__name__ not in ['bool']:
            raise ValueError(
                "logistic_param's decay_sqrt {} not supported, should be 'bool'".format(
                    self.decay_sqrt))
        self.stepwise_param.check()

        if self.validation_freqs is not None:
            if type(self.validation_freqs).__name__ not in ["int", "list", "tuple", "set"]:
                raise ValueError(
                    "validation strategy param's validate_freqs's type not supported , should be int or list or tuple or set"
                )
            if type(self.validation_freqs).__name__ == "int" and self.validation_freqs <= 0:
                raise ValueError("validation strategy param's validate_freqs should greater than 0")

        if self.early_stopping_rounds is None:
            pass
        elif isinstance(self.early_stopping_rounds, int):
            if self.early_stopping_rounds < 1:
                raise ValueError("early stopping rounds should be larger than 0 when it's integer")
            if self.validation_freqs is None:
                raise ValueError("validation freqs must be set when early stopping is enabled")

        if self.metrics is not None and not isinstance(self.metrics, list):
            raise ValueError("metrics should be a list")

        if not isinstance(self.use_first_metric_only, bool):
            raise ValueError("use_first_metric_only should be a boolean")

        if self.floating_point_precision is not None and \
                (not isinstance(self.floating_point_precision, int) or\
                 self.floating_point_precision < 0 or self.floating_point_precision > 63):
            raise ValueError("floating point precision should be null or a integer between 0 and 63")

        self.review_strategy = self.review_strategy.lower()
        self.check_valid_value(self.review_strategy, descr, ["respectively", "all_review_in_guest"])
        if not consts.ALLOW_REVIEW_GUEST_ONLY and self.review_strategy == "all_review_in_guest":
            raise PermissionError("review strategy: all_review_in_guest has not been authorized.")
        return True