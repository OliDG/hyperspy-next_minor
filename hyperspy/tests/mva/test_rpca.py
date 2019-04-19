import numpy as np
import scipy.linalg
import pytest

from hyperspy.learn.rpca import rpca_godec, orpca
from hyperspy.misc.machine_learning.import_sklearn import fast_svd


class TestRPCA:

    def setup_method(self, method):
        # Define shape etc.
        m = 256  # Dimensionality
        n = 250  # Number of samples
        r = 3
        s = 0.01

        # Low-rank, sparse and noise matrices
        rng = np.random.RandomState(101)
        U = scipy.linalg.orth(rng.randn(m, r))
        V = rng.randn(n, r)
        A = np.dot(U, V.T)
        E = 10 * rng.binomial(1, s, (m, n))
        G = 0.01 * rng.randn(m, n)
        X = A + E + G

        self.m = m
        self.n = n
        self.rank = r
        self.lambda1 = 0.01
        self.A = A
        self.X = X

        # Test tolerance
        self.tol = 1e-3

    def test_default(self):
        X, E, G, U, S, V = rpca_godec(self.X, rank=self.rank)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_power(self):
        X, E, G, U, S, V = rpca_godec(self.X, rank=self.rank, power=1)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_iter(self):
        X, E, G, U, S, V = rpca_godec(self.X, rank=self.rank, maxiter=1e4)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_tol(self):
        X, E, G, U, S, V = rpca_godec(self.X, rank=self.rank, tol=1e-4)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_regularization(self):
        X, E, G, U, S, V = rpca_godec(
            self.X, rank=self.rank, lambda1=self.lambda1)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol


class TestORPCA:

    def setup_method(self, method):
        # Define shape etc.
        m = 256  # Dimensionality
        n = 1024  # Number of samples
        r = 3
        s = 0.01

        # Low-rank and sparse error matrices
        rng = np.random.RandomState(101)
        U = scipy.linalg.orth(rng.randn(m, r))
        V = rng.randn(n, r)
        A = np.dot(U, V.T)
        E = 10 * rng.binomial(1, s, (m, n))
        X = A + E

        self.m = m
        self.n = n
        self.rank = r
        self.lambda1 = 1.0 / np.sqrt(n)
        self.lambda2 = 1.0 / np.sqrt(n)
        self.A = A
        self.X = X
        self.subspace_learning_rate = 1.1
        self.training_samples = 32
        self.subspace_momentum = 0.1

        # Test tolerance
        self.tol = 3e-3

    def test_default(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    @pytest.mark.skipif(
        fast_svd is None,
        reason="fastsvd required sklearn which is not installed")
    def test_fast(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank, fast=True)
        # Only check shapes
        assert X.shape == (self.m, self.n)
        assert E.shape == (self.m, self.n)
        assert U.shape == (self.m, self.rank)
        assert S.shape == (self.rank,)
        assert V.shape == (self.n, self.rank)

    def test_method_BCD(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank, method='BCD')

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_method_SGD(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank,
                              method='SGD', subspace_learning_rate=self.subspace_learning_rate)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_method_MomentumSGD(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank,
                              method='MomentumSGD',
                              subspace_learning_rate=self.subspace_learning_rate,
                              subspace_momentum=self.subspace_momentum)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_init(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank, init='rand')

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol

    def test_training(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank, init='qr',
                              training_samples=self.training_samples)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        print(normX)
        assert normX < self.tol

    def test_regularization(self):
        X, E, U, S, V = orpca(self.X, rank=self.rank,
                              lambda1=self.lambda1,
                              lambda2=self.lambda2)

        # Check the low-rank component MSE
        normX = np.linalg.norm(X - self.A) / (self.m * self.n)
        assert normX < self.tol
