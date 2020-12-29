import sys, os
os.path.abspath(os.path.join('..', './representation'))
from representation.code2vector import Code2vector
import pickle
from representation.CC2Vec import lmg_cc2ftr_interface
import os
from bert_serving.client import BertClient
from gensim.models import word2vec,Doc2Vec
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import *
# Imports and method code2vec
from representation.code2vector import Code2vector
from representation.code2vec.vocabularies import VocabType
from representation.code2vec.config import Config
from representation.code2vec.model_base import Code2VecModelBase
import numpy as np

MODEL_MODEL_LOAD_PATH = '/Users/haoye.tian/Documents/University/data/models/java14_model/saved_model_iter8.release'
MODEL_CC2Vec = '../representation/CC2Vec/'

class Word2vector:
    def __init__(self, test_w2v=None, patch_w2v=None, path_patch_root=None):
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
        elif self.patch_w2v == 'bert':
            self.m = BertClient(check_length=False, check_version=False)


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
                if self.patch_w2v == 'cc2vec':
                    learned_vector = lmg_cc2ftr_interface.learned_feature(path_patch_id, load_model=MODEL_CC2Vec + 'cc2ftr.pt', dictionary=self.dictionary)
                    learned_vector = list(learned_vector.flatten())
                elif self.patch_w2v == 'bert':
                    learned_vector = self.learned_feature(path_patch_id, self.patch_w2v)
                multi_vector.append(learned_vector)
            patch_vector = np.array(multi_vector).mean(axis=0)
        except Exception as e:
            raise

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

    def convert_single_patch(self, path_patch):
        multi_vector = []
        patch = os.listdir(path_patch)
        for part in patch:
            p = os.path.join(path_patch, part)
            learned_vector = lmg_cc2ftr_interface.learned_feature(p, load_model=MODEL_CC2Vec + 'cc2ftr.pt', dictionary=self.dictionary)
            multi_vector.append(list(learned_vector.flatten()))

        combined_vector = np.array(multi_vector).mean(axis=0)
        return combined_vector

    def learned_feature(self, path_patch, w2v):
        try:
            bugy_all = self.get_diff_files_frag(path_patch, type='patched')
            patched_all = self.get_diff_files_frag(path_patch, type='buggy')
        except Exception as e:
            print('name: {}, exception: {}'.format(path_patch, e))
            return []

        # tokenize word
        bugy_all_token = word_tokenize(bugy_all)
        patched_all_token = word_tokenize(patched_all)

        try:
            bug_vec, patched_vec = self.output_vec(w2v, bugy_all_token, patched_all_token)
        except Exception as e:
            print('name: {}, exception: {}'.format(path_patch, e))
            return []

        bug_vec = bug_vec.reshape((1, -1))
        patched_vec = patched_vec.reshape((1, -1))

        # embedding feature cross
        subtract, multiple, cos, euc = self.multi_diff_features(bug_vec, patched_vec)
        # embedding = subtract

        embedding = np.hstack((subtract, multiple, cos, euc,))

        return list(embedding.flatten())

    def subtraction(self, buggy, patched):
        return buggy - patched

    def multiplication(self, buggy, patched):
        return buggy * patched

    def cosine_similarity(self, buggy, patched):
        return paired_cosine_distances(buggy, patched)

    def euclidean_similarity(self, buggy, patched):
        return paired_euclidean_distances(buggy, patched)

    def multi_diff_features(self, buggy, patched):
        subtract = self.subtraction(buggy, patched)
        multiple = self.multiplication(buggy, patched)
        cos = self.cosine_similarity(buggy, patched).reshape((1, 1))
        euc = self.euclidean_similarity(buggy, patched).reshape((1, 1))

        return subtract, multiple, cos, euc

    def output_vec(self, w2v, bugy_all_token, patched_all_token):

        if w2v == 'Bert':
            bug_vec = self.m.encode([bugy_all_token], is_tokenized=True)
            patched_vec = self.m.encode([patched_all_token], is_tokenized=True)
        elif w2v == 'Doc':
            # m = Doc2Vec.load('../model/doc_file_64d.model')
            m = Doc2Vec.load('../model/Doc_frag_ASE.model')
            bug_vec = m.infer_vector(bugy_all_token, alpha=0.025, steps=300)
            patched_vec = m.infer_vector(patched_all_token, alpha=0.025, steps=300)
        else:
            print('wrong model')
            raise

        return bug_vec, patched_vec

    def get_diff_files_frag(self, path_patch, type):
        with open(path_patch, 'r') as file:
            lines = ''
            p = r"([^\w_])"
            flag = True
            # try:
            for line in file:
                line = line.strip()
                if '*/' in line:
                    flag = True
                    continue
                if flag == False:
                    continue
                if line != '':
                    if line.startswith('@@') or line.startswith('diff') or line.startswith('index'):
                        continue
                    if line.startswith('Index') or line.startswith('==='):
                        continue
                    elif '/*' in line:
                        flag = False
                        continue
                    elif type == 'buggy':
                        if line.startswith('---') or line.startswith('PATCH_DIFF_ORIG=---'):
                            continue
                            # line = re.split(pattern=p, string=line.split(' ')[1].strip())
                            # lines += ' '.join(line) + ' '
                        elif line.startswith('-'):
                            if line[1:].strip().startswith('//'):
                                continue
                            line = re.split(pattern=p, string=line[1:].strip())
                            line = [x.strip() for x in line]
                            while '' in line:
                                line.remove('')
                            line = ' '.join(line)
                            lines += line.strip() + ' '
                        elif line.startswith('+'):
                            # do nothing
                            pass
                        else:
                            line = re.split(pattern=p, string=line.strip())
                            line = [x.strip() for x in line]
                            while '' in line:
                                line.remove('')
                            line = ' '.join(line)
                            lines += line.strip() + ' '
                    elif type == 'patched':
                        if line.startswith('+++'):
                            continue
                            # line = re.split(pattern=p, string=line.split(' ')[1].strip())
                            # lines += ' '.join(line) + ' '
                        elif line.startswith('+'):
                            if line[1:].strip().startswith('//'):
                                continue
                            line = re.split(pattern=p, string=line[1:].strip())
                            line = [x.strip() for x in line]
                            while '' in line:
                                line.remove('')
                            line = ' '.join(line)
                            lines += line.strip() + ' '
                        elif line.startswith('-'):
                            # do nothing
                            pass
                        else:
                            line = re.split(pattern=p, string=line.strip())
                            line = [x.strip() for x in line]
                            while '' in line:
                                line.remove('')
                            line = ' '.join(line)
                            lines += line.strip() + ' '
            # except Exception:
            #     print(Exception)
            #     return 'Error'
            return lines