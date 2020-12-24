import sys, os
os.path.abspath(os.path.join('..', './representation'))
from representation.code2vector import Code2vector
import pickle
from representation.CC2Vec import lmg_cc2ftr_interface
import os
# Imports and method code2vec
from representation.code2vector import Code2vector
from representation.code2vec.vocabularies import VocabType
from representation.code2vec.config import Config
from representation.code2vec.model_base import Code2VecModelBase
import numpy as np

MODEL_MODEL_LOAD_PATH = '/Users/haoye.tian/Documents/University/data/models/java14_model/saved_model_iter8.release'
MODEL_CC2Vec = '../representation/CC2Vec/'

class Word2vector:
    def __init__(self, test_w2v, patch_w2v, path_patch_root=None):
        # self.w2v = word2vec
        self.test_w2v = test_w2v
        self.patch_w2v = patch_w2v
        self.path_patch_root = path_patch_root

        if self.test_w2v == 'code2vec':
            # Init and Load the model
            config = Config(set_defaults=True, load_from_args=True, verify=False)
            config.MODEL_LOAD_PATH = MODEL_MODEL_LOAD_PATH
            config.EXPORT_CODE_VECTORS = True
            model = Word2vector.load_model_code2vec_dynamically(config)
            config.log('Done creating code2vec model')
            self.c2v = Code2vector(model)
            # =======================
        if self.patch_w2v == 'cc2vec':
            self.dictionary = pickle.load(open(MODEL_CC2Vec+'dict.pkl', 'rb'))

    @staticmethod
    def load_model_code2vec_dynamically(config: Config) -> Code2VecModelBase:
        assert config.DL_FRAMEWORK in {'tensorflow', 'keras'}
        if config.DL_FRAMEWORK == 'tensorflow':
            from representation.code2vec.tensorflow_model import Code2VecModel
        elif config.DL_FRAMEWORK == 'keras':
            from representation.code2vec.keras_model import Code2VecModel
        return Code2VecModel(config)

    def convert_both(self, test_name, test_text, patch_ids):
        try:
            #1 test case function
            function = test_text
            test_vector = self.c2v.convert(function)

            #2 patch ids
            # find path_patch
            if len(patch_ids) == 1 and patch_ids[0].endswith('-one'):
                project = patch_ids[0].split('_')[0]
                id = patch_ids[0].split('_')[1].replace('-one', '')
                path_patch = self.path_patch_root + project + '/' + id + '/'
                patch_ids = os.listdir(path_patch)
                path_patch_ids = [path_patch + patch_id for patch_id in patch_ids]
            else:
                path_patch_ids = []
                for name in patch_ids:
                    project = name.split('_')[0]
                    id = name.split('_')[1]
                    patch_id = name.split('_')[1] + '_' + name.split('_')[2] + '.patch'
                    path_patch = self.path_patch_root + project + '/' + id + '/'
                    path_patch_ids.append(os.path.join(path_patch, patch_id))

            multi_vector = []
            for path_patch_id in path_patch_ids:
                learned_vector = lmg_cc2ftr_interface.learned_feature(path_patch_id, load_model=MODEL_CC2Vec + 'cc2ftr.pt', dictionary=self.dictionary)
                multi_vector.append(list(learned_vector.flatten()))
            patch_vector = np.array(multi_vector).mean(axis=0)
        except Exception as e:
            raise e

        return test_vector, patch_vector

    def convert(self, test_name, data_text):
        if self.test_w2v == 'code2vec':
            test_vector = []
            for i in range(len(data_text)):
                function = data_text[i]
                try:
                    vector = self.c2v.convert(function)
                except Exception as e:
                    print('{} test_name:{} Exception:{}'.format(i, test_name[i], 'Wrong syntax'))
                    continue
                print('{} test_name:{}'.format(i, test_name[i]))
                test_vector.append(vector)
            return test_vector

        if self.patch_w2v == 'cc2vec':
            patch_vector = []
            for i in range(len(data_text)):
                patch_ids = data_text[i]
                # find path_patch
                if len(patch_ids) == 1 and patch_ids[0].endwith('-one'):
                    project = patch_ids[0].split('_')[0]
                    id = patch_ids[0].split('_')[1].replace('-one','')
                    path_patch = self.path_patch_root + project +'/'+ id + '/'
                    patch_ids = os.listdir(path_patch)
                    path_patch_ids = [path_patch + patch_id for patch_id in patch_ids]
                else:
                    path_patch_ids = []
                    for name in patch_ids:
                        project = name.split('_')[0]
                        id = name.split('_')[1]
                        patch_id = name.split('_')[1] +'_'+ name.split('_')[2] + '.patch'
                        path_patch = self.path_patch_root + project +'/'+ id + '/'
                        path_patch_ids.append(os.path.join(path_patch, patch_id))

                multi_vector = []
                for path_patch_id in path_patch_ids:
                    learned_vector = lmg_cc2ftr_interface.learned_feature(path_patch_id, load_model=MODEL_CC2Vec+'cc2ftr.pt', dictionary=self.dictionary)
                    multi_vector.append(list(learned_vector.flatten()))
                combined_vector = np.array(multi_vector).mean(axis=0)
                patch_vector.append(combined_vector)
            return patch_vector
