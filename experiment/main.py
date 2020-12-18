import sys, os
sys.path.append(os.path.abspath(os.path.join('..', '.')))

import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler

from experiment.config import Config
from representation.word2vector import Word2vector
import numpy as np
from sklearn.cluster import KMeans

class Experiment:
    def __init__(self, path_test, path_patch):
        self.path_test = path_test
        self.path_patch = path_patch

        self.test_data = None
        self.patch_data = None
        self.test_vector = None
        self.patch_vector = None

    def load_test(self,):
        with open(self.path_test,'rb') as f:
            self.test_data = pickle.load(f)

        # self.patch_data = pickle.load(self.path_patch)

    def run(self):
        self.load_test()

        self.test2vector(word2v='code2vec')
        # self.patch2vector(word2v='cc2vec')

        self.cal_all_simi(self.test_vector)

        self.cluster_dist(self.test_vector)

    def test2vector(self, word2v='code2vec'):
        w2v = Word2vector(word2v)
        test_function = self.test_data[3]
        test_name = self.test_data[0]
        self.test_vector = w2v.convert(test_name, test_function)
        print('test vector done')

    def patch2vector(self, word2v='cc2vec'):
        w2v = Word2vector(word2v)
        self.patch_vector = w2v.convert(self.patch_data)

    def cal_all_simi(self, test_vector):
        test_vector = np.array(test_vector)
        center = np.mean(test_vector, axis=0)
        dists = [np.linalg.norm(vec - center) for vec in test_vector]
        average = np.array(dists).mean()
        print('one cluster average distance: {}'.format(average))

    def cluster_dist(self, test_vector):
        self.cluster(test_vector)

    def cluster(self, test_vector):
        scaler = StandardScaler()
        X = pd.DataFrame(scaler.fit_transform(test_vector))

        kmeans = KMeans(n_clusters=4)
        # kmeans.fit(np.array(test_vector))
        clusters = kmeans.fit_predict(test_vector)

        X["Cluster"] = clusters

if __name__ == '__main__':
    config = Config()
    path_test = config.path_test
    path_patch = config.path_patch

    e = Experiment(path_test, path_patch)
    e.run()