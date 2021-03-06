# coding=utf-8
# Copyright 2020 The Uncertainty Baselines Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""SVHN dataset builder."""

from typing import Any, Dict, Optional

import tensorflow.compat.v2 as tf
import tensorflow_datasets as tfds
from uncertainty_baselines.datasets import base


class SvhnDataset(base.BaseDataset):
  """SVHN dataset builder class."""

  def __init__(
      self,
      batch_size: int,
      eval_batch_size: int,
      shuffle_buffer_size: int = None,
      num_parallel_parser_calls: int = 64,
      data_dir: Optional[str] = None,
      normalize_by_cifar: bool = False,
      **unused_kwargs: Dict[str, Any]):
    """Create a SVHN tf.data.Dataset builder.

    Args:
      batch_size: the training batch size.
      eval_batch_size: the validation and test batch size.
      shuffle_buffer_size: the number of example to use in the shuffle buffer
        for tf.data.Dataset.shuffle().
      num_parallel_parser_calls: the number of parallel threads to use while
        preprocessing in tf.data.Dataset.map().
      data_dir: optional dir to save TFDS data to. If none then the local
        filesystem is used. Required for using TPUs on Cloud.
      normalize_by_cifar: whether or not to normalize each image by the CIFAR
        dataset mean and stddev.
    """
    self._normalize_by_cifar = normalize_by_cifar
    _, info = tfds.load('svhn_cropped', with_info=True)
    super(SvhnDataset, self).__init__(
        name='svhn_cropped',
        num_train_examples=50000,
        num_validation_examples=info.splits['train'].num_examples - 50000,
        num_test_examples=info.splits['test'].num_examples,
        batch_size=batch_size,
        eval_batch_size=eval_batch_size,
        shuffle_buffer_size=shuffle_buffer_size,
        num_parallel_parser_calls=num_parallel_parser_calls,
        data_dir=data_dir)

  def _read_examples(self, split: base.Split) -> tf.data.Dataset:
    """We use the original 'validation' set as test."""
    if split == base.Split.TRAIN:
      train_split = tfds.core.ReadInstruction(
          'train', to=-self._num_validation_examples, unit='abs')
      return tfds.load(
          'svhn_cropped',
          split=train_split,
          **self._tfds_kwargs)
    elif split == base.Split.VAL:
      val_split = tfds.core.ReadInstruction(
          'train', from_=-self._num_validation_examples, unit='abs')
      return tfds.load(
          'svhn_cropped',
          split=val_split,
          **self._tfds_kwargs)
    elif split == base.Split.TEST:
      return tfds.load(
          'svhn_cropped',
          split='test',
          **self._tfds_kwargs)
    else:
      raise ValueError(
          'Invalid dataset split in _read_examples: {}'.format(split))

  def _create_process_example_fn(self, split: base.Split) -> base.PreProcessFn:
    del split

    def _example_parser(example: Dict[str, tf.Tensor]) -> Dict[str, tf.Tensor]:
      """A pre-process function to return images in [0, 1]."""
      image = example['image']
      image = tf.image.convert_image_dtype(image, tf.float32)
      label = tf.cast(example['label'], tf.int32)
      if self._normalize_by_cifar:
        mean = tf.constant([0.4914, 0.4822, 0.4465])
        std = tf.constant([0.2023, 0.1994, 0.2010])
        image = (image - mean) / std
      parsed_example = {
          'features': image,
          'labels': label,
      }
      return parsed_example

    return _example_parser
