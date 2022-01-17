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


@pytest.mark.parametrize('stimulus_set_identifier', [
    pytest.param('dicarlo.hvm', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.hvm-public', marks=[]),
    pytest.param('dicarlo.hvm-private', marks=[pytest.mark.private_access]),
    pytest.param('tolias.Cadena2017', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.naturalistic', marks=[pytest.mark.private_access]),
    pytest.param('dicarlo.BashivanKar2019.synthetic', marks=[pytest.mark.private_access]),
])
def test_existence(stimulus_set_identifier):
    assert brainio.get_stimulus_set(stimulus_set_identifier) is not None



