#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import os
from unittest.mock import MagicMock

import pytest
from hydra import compose, initialize

# import numpy as np
from abses import Actor, MainModel
from src.env import CompetingCell
from src.hunter import Hunter
from src.people import SiteGroup

# 加载项目层面的配置
with initialize(version_base=None, config_path="../config"):
    cfg = compose(config_name="config")
os.chdir(cfg.root)

MAX_SIZE = cfg.hunter.max_size
MIN_SIZE = cfg.hunter.min_size
G_RATE = cfg.hunter.growth_rate


class Farmer(Actor):
    """用于测试的农民类"""


class TestHunter:
    """测试狩猎采集者"""

    @pytest.fixture(name="cell")
    def mock_cell(self):
        """一个虚假的斑块"""
        model = MainModel(parameters=cfg)
        layer = model.nature.create_module(
            how="from_resolution",
            shape=(4, 4),
            cell_cls=CompetingCell,
        )
        cell = layer.array_cells[3][3]
        # 模拟最大可支持的人口规模
        cell.lim_h = cfg.hunter.settle_size
        # 创建一个农民，放到它旁边
        farmer = model.agents.create(Farmer, singleton=True)
        farmer.put_on(layer.array_cells[3][2])
        return cell

    @pytest.fixture(name="group")
    def site_group(self):
        """原始的聚落"""
        # size = np.random.uniform(30, 60)
        model = MainModel(parameters=cfg)
        return model.agents.create(Hunter, size=50, singleton=True)

    @pytest.mark.parametrize(
        "size, expected, settled",
        [
            (100, 100, False),
            (0, MIN_SIZE, False),
            (500, 500, True),
            (7000, MAX_SIZE, True),
        ],
        ids=["positive_size", "zero_size", "max_size", "large_size"],
    )
    def test_size_property(self, group, size, expected, settled):
        """测试人口规模有最大最小值限制"""
        # Arrange
        group.size = size

        # Act
        result = group.size

        # Assert
        assert result == expected
        assert group.is_complex is settled

    @pytest.mark.parametrize(
        "growth_rate, initial_size, expected",
        [
            (0.1, 100, 110),
            (0.2, 0, 7),
            (-0.1, 500, 450),
            (0.5, 1000, 1500),
        ],
        ids=["positive_growth", "zero_growth", "negative_growth", "large_growth"],
    )
    def test_population_growth(self, group, growth_rate, initial_size, expected):
        """测试人口增长"""
        # Arrange
        group.size = initial_size

        # Act
        group.population_growth(growth_rate)

        # Assert
        assert group.size == expected

    @pytest.mark.parametrize(
        "s_min, s_max, initial_size, expected_size, expected_new_group_size",
        [
            (50, 50, 100, 50, 50),
            (200, 300, 99, 99, None),
            # (100, 200, 100, 0, 100),  # TODO 测试一个很极端的情况
        ],
        ids=[
            "within_range",
            "above_max_size",
            # "below_min_size"
        ],
    )
    def test_diffuse(
        self,
        group,
        cell,
        s_min,
        s_max,
        initial_size,
        expected_size,
        expected_new_group_size,
    ):
        """测试人口分散，随机选择一个最小和最大的规模，分裂出去"""
        # Arrange
        group.put_on(cell)
        group.params.new_group_size = (s_min, s_max)
        group.size = initial_size
        assert group.size == initial_size
        assert group.loc("lim_h") == cfg.hunter.settle_size

        # Act
        new_group = group.diffuse()

        # Assert
        assert group.size == expected_size
        assert getattr(new_group, "size", None) == expected_new_group_size

    # @pytest.mark.parametrize(
    #     ""
    # )

    @pytest.mark.parametrize(
        "convert_prob, random_value, arable, changed",
        [
            (0.5, 0.4, True, True),
            (0.5, 0.6, True, False),
            (0.1, 0.05, False, False),
            (0.1, 0.2, False, False),
        ],
        ids=["convert", "no_convert", "convert_low_prob", "no_convert_high_prob"],
    )
    def test_convert(self, cell, group, convert_prob, random_value, changed, arable):
        """测试当小于一定概率时，农民与狩猎采集者可能发生相互转化"""
        # Arrange
        group.params.convert_prob = convert_prob
        group.random.random = MagicMock(return_value=random_value)
        group.put_on(cell)
        # 配置是否是可耕地的条件
        cell.slope = 5
        cell.aspect = 100
        cell.elevation = 100 if arable else 300

        size = group.size
        # Act
        convert = group.convert()

        # Assert
        assert isinstance(convert, SiteGroup)
        assert (isinstance(convert, Hunter)) != changed
        assert convert.size == size
