from representation.code2vector import Code2vector
import pickle
from representation.CC2Vec import lmg_cc2ftr_interface

# Imports and method code2vec
from code2vector import Code2vector
from code2vec.vocabularies import VocabType
from code2vec.config import Config
from code2vec.model_base import Code2VecModelBase

MODEL_MODEL_LOAD_PATH = '/Users/abdoulkader.kabore/snt/PhD/01/PatchSimilarity/data/code2vec/models/java14_model/saved_model_iter8.release'

class Word2vector:
    def __init__(self, word2vec):
        self.w2v = word2vec
        if self.w2v == 'code2vec':
            # Init and Load the model
            config = Config(set_defaults=True, load_from_args=True, verify=False)
            config.MODEL_LOAD_PATH = MODEL_MODEL_LOAD_PATH
            config.EXPORT_CODE_VECTORS = True
            model = Word2vector.load_model_code2vec_dynamically(config)
            config.log('Done creating code2vec model')
            self.c2v = Code2vector(model)
            # =======================

    @staticmethod
    def load_model_code2vec_dynamically(config: Config) -> Code2VecModelBase:
        assert config.DL_FRAMEWORK in {'tensorflow', 'keras'}
        if config.DL_FRAMEWORK == 'tensorflow':
            from code2vec.tensorflow_model import Code2VecModel
        elif config.DL_FRAMEWORK == 'keras':
            from code2vec.keras_model import Code2VecModel
        return Code2VecModel(config)

    def convert(self, data_text):
        if self.w2v == 'code2vec':
            test_vector = []
            for i in range(len(data_text)):
                function = data_text[i]
                vector = self.c2v.convert(function)
                test_vector.append(vector)
                break
            return test_vector

        if self.w2v == 'cc2vec':
            dictionary = pickle.load(open('../CC2Vec/dict.pkl', 'rb'))
            patch_vector = []
            for i in range(len(data_text)):
                path_patch = data_text[i]
                learned_vector = lmg_cc2ftr_interface.learned_feature(path_patch, load_model='../CC2Vec/cc2ftr.pt', dictionary=dictionary)
                patch_vector.append(learned_vector)
            return patch_vector
