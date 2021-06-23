import os

import imageio
import numpy as np
import pandas as pd
import pytest

import brainio
from brainio.stimuli import StimulusSet


class TestPreservation:
    def test_subselection(self):
        stimulus_set = StimulusSet([{'image_id': i} for i in range(100)])
        stimulus_set.image_paths = {i: f'/dummy/path/{i}' for i in range(100)}
        stimulus_set = stimulus_set[stimulus_set['image_id'].isin(stimulus_set['image_id'].values[:3])]
        assert stimulus_set.get_image(0) is not None

    def test_pd_concat(self):
        s1 = StimulusSet([{'image_id': i} for i in range(10)])
        s1.image_paths = {i: f'/dummy/path/{i}' for i in range(10)}
        s2 = StimulusSet([{'image_id': i} for i in range(10, 20)])
        s2.image_paths = {i: f'/dummy/path/{i}' for i in range(10, 20)}
        s = pd.concat((s1, s2))
        s.image_paths = {**s1.image_paths, **s2.image_paths}
        assert s.get_image(1) is not None
        assert s.get_image(11) is not None


def test_get_stimulus_set():
    stimulus_set = brainio.get_stimulus_set("dicarlo.hvm-public")
    assert "image_id" in stimulus_set.columns
    assert set(stimulus_set.columns).issuperset({'image_id', 'object_name', 'variation', 'category_name',
                                                 'image_file_name', 'background_id', 'ty', 'tz',
                                                 'size', 'id', 's', 'rxz', 'ryz', 'ryz_semantic',
                                                 'rxy', 'rxy_semantic', 'rxz_semantic'})
    assert len(stimulus_set) == 3200
    assert stimulus_set.identifier == 'dicarlo.hvm-public'
    for image_id in stimulus_set['image_id']:
        image_path = stimulus_set.get_image(image_id)
        assert os.path.exists(image_path)
        extension = os.path.splitext(image_path)[1]
        assert extension in ['.png', '.PNG', '.jpg', '.jpeg', '.JPG', '.JPEG']


def test_loadname_dicarlo_hvm():
    assert brainio.get_stimulus_set(identifier="dicarlo.hvm-public") is not None


class TestLoadImage:
    def test_dicarlohvm(self):
        stimulus_set = brainio.get_stimulus_set(identifier="dicarlo.hvm-public")
        paths = stimulus_set.image_paths.values()
        for path in paths:
            image = imageio.imread(path)
            assert isinstance(image, np.ndarray)
            assert image.size > 0


@pytest.mark.parametrize('stimulus_set', (
        'dicarlo.hvm',
        'dicarlo.hvm-public',
        'dicarlo.hvm-private',
        'gallant.David2004',
        'tolias.Cadena2017',
        'movshon.FreemanZiemba2013',
        'movshon.FreemanZiemba2013-public',
        'movshon.FreemanZiemba2013-private',
        'dicarlo.objectome.public',
        'dicarlo.objectome.private',
        'dicarlo.Kar2018cocogray',
        'klab.Zhang2018.search_obj_array',
        'dicarlo.Rajalingham2020',
        'dicarlo.Rust2012',
        'dicarlo.BOLD5000',
        'dicarlo.THINGS1',
        'dicarlo.THINGS2',
        'aru.Kuzovkin2018',
        'dietterich.Hendrycks2019.noise',
        'dietterich.Hendrycks2019.blur',
        'dietterich.Hendrycks2019.weather',
        'dietterich.Hendrycks2019.digital',
        'fei-fei.Deng2009',
        'aru.Cichy2019',
        'dicarlo.BashivanKar2019.naturalistic',
        'dicarlo.BashivanKar2019.synthetic'
))
def test_list_stimulus_set(stimulus_set):
    l = brainio.list_stimulus_sets()
    assert stimulus_set in l


@pytest.mark.private_access
def test_klab_Zhang2018search():
    stimulus_set = brainio.get_stimulus_set('klab.Zhang2018.search_obj_array')
    # There are 300 presentation images in the assembly but 606 in the StimulusSet (explanation from @shashikg follows).
    # For each of the visual search task out of total 300, you need two images (one - the target image,
    # second - the search space image) plus there are 6 different mask images to mask objects
    # present at 6 different locations in a specified search image.
    # Therefore, a total of 300 * 2 + 6 images are there in the stimulus set.
    assert len(stimulus_set) == 606
    assert len(set(stimulus_set['image_id'])) == 606


@pytest.mark.private_access
@pytest.mark.slow
class TestDietterichHendrycks2019:
    def test_noise(self):
        stimulus_set = brainio.get_stimulus_set('dietterich.Hendrycks2019.noise')
        assert len(stimulus_set) == 3 * 5 * 50000
        assert len(set(stimulus_set['synset'])) == 1000

    def test_blur(self):
        stimulus_set = brainio.get_stimulus_set('dietterich.Hendrycks2019.blur')
        assert len(stimulus_set) == 4 * 5 * 50000
        assert len(set(stimulus_set['synset'])) == 1000

    def test_weather(self):
        stimulus_set = brainio.get_stimulus_set('dietterich.Hendrycks2019.weather')
        assert len(stimulus_set) == 4 * 5 * 50000
        assert len(set(stimulus_set['synset'])) == 1000

    def test_digital(self):
        stimulus_set = brainio.get_stimulus_set('dietterich.Hendrycks2019.digital')
        assert len(stimulus_set) == 4 * 5 * 50000
        assert len(set(stimulus_set['synset'])) == 1000


@pytest.mark.private_access
def test_feifei_Deng2009():
    stimulus_set = brainio.get_stimulus_set('fei-fei.Deng2009')
    assert len(stimulus_set) == 50_000
    assert len(set(stimulus_set['label'])) == 1_000
