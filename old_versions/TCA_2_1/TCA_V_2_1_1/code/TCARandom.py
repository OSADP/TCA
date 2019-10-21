import random
import unittest

class Random_generator(object):

    def __init__(self, seed=1):
        self.generator = {}

        if seed is not None:
            self.masterseed = random.Random()
            self.masterseed.seed(seed)
        else:
            self.masterseed = random.Random()

        self.psn=[]


    def add_generator_range(self, title, start, end):
        if isinstance(title,str):
            rand = random.Random()
            rand.seed(self.masterseed.random())
            self.generator[title] = (rand, start, end)


    def __getitem__(self, title):
        if title in self.generator.keys() and isinstance(title, str):
                return self.generator[title][0].randint(self.generator[title][1],self.generator[title][2])


class Random_Generator_Tests(unittest.TestCase):

    def setUp(self):
        pass

    def test_seed(self):

        rgen = Random_generator(123456)
        rgen.add_generator_range('stop_time', 0, 300)
        rgen.add_generator_range('distance', 300, 600)
        st = []
        d = []
        for i in range(10):
            st.append(rgen['stop_time'])
            d.append(rgen['distance'])

        rgen2 = Random_generator(123456)
        rgen2.add_generator_range('stop_time', 0, 300)
        rgen2.add_generator_range('distance', 300, 600)
        nst = []
        nd = []
        for i in range(10):
            nst.append(rgen2['stop_time'])
            nd.append(rgen2['distance'])

        assert nst == st
        assert nd == d

    def test_random(self):
        rgen = Random_generator()
        rgen.add_generator_range('xxxx', 1, 100)

        l = []
        for i in range(1000):
            l.append(rgen['xxxx'])
        assert max(l)<101
        assert min(l)>0



if __name__ == '__main__':
    unittest.main()






