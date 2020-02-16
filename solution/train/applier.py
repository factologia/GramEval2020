# -*- coding: utf-8 -*-

import json
import logging
import os
import torch

from tqdm import tqdm

from allennlp.data.vocabulary import Vocabulary

from train.main import Config, _build_model, _get_reader
from train.lemmatize_helper import LemmatizeHelper

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')

    data_dir = '../data/test_data'
    model_name = 'parser_with_tagger'
    model_dir = os.path.join('../models', model_name)
    result_data_dir = os.path.join('../predictions/', model_name)

    if not os.path.isdir(result_data_dir):
        os.makedirs(result_data_dir)

    with open(os.path.join(model_dir, 'config.json')) as f:
        config = Config(**json.load(f))

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu:0')

    vocab = Vocabulary.from_files(os.path.join(model_dir, 'vocab'))
    lemmatize_helper = LemmatizeHelper.load(model_dir)

    model = _build_model(config, vocab, lemmatize_helper).to(device)
    model.load_state_dict(torch.load(os.path.join(model_dir, 'best.th'), map_location=device))

    reader = _get_reader(config)

    for path in os.listdir(data_dir):
        data = reader.read(os.path.join(data_dir, path))
        with open(os.path.join(result_data_dir, path), 'w') as f_out:
            for instance in tqdm(data, desc=path):
                predictions = model.forward_on_instance(instance)
                for token_index in range(len(predictions['words'])):
                    word = predictions['words'][token_index]
                    lemma = predictions['predicted_lemmas'][token_index]
                    upos, feats = predictions['predicted_gram_vals'][token_index].split('|', 1)
                    head_tag = predictions['predicted_dependencies'][token_index]
                    head_index = predictions['predicted_heads'][token_index]

                    print(token_index + 1, word, lemma, upos, '_', feats,
                          head_index, head_tag, '_', '_', sep='\t', file=f_out)
                print(file=f_out)


if __name__ == "__main__":
    main()
