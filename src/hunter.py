#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.nature import PatchCell
from src.people import SiteGroup


class Hunter(SiteGroup):
    """狩猎采集者"""

    @property
    def moving(self) -> bool:
        """关于移动力大小的讨论尺度都太小，或许可以简化为1次移动1格，把差异落在狩猎采集者是否定居，即丧失移动力。后者可大致设定为size_h大于100（Kelly 2013: 171）"""
        return self.size > self.params.settle_size

    def diffuse(self):
        """如果人口大于一定规模，狩猎采集者分散出去"""
        if self.size >= self.loc("lim_h"):
            super().diffuse()

    def convert(self):
        """周围有其他农民"""
        # 周围有农民
        cells = self._cell.sphere(radius=1, moor=True)
        cond1 = cells.has_agent({"breed": "Farmer"})
        # 且目前的土地是可耕地
        cond2 = self._cell.is_arable
        # 同时满足上述条件，狩猎采集者转化为农民
        if cond1 and cond2:
            super().convert()

    def move(self):
        """有移动能力才能移动，在周围随机选取一个格子移动"""
        if self.moving:
            # TODO 怎么移动？周围随机 r=1,2,3,..
            cells = self._cell.sphere(radius=1, neigh_4=True)
            cell = cells.select({"has_hunter": False}).random_choose()
            self.put_on(cell)

    def _loss_competition(self, loser: SiteGroup):
        """失败者"""
        loss = self.model.loss_rate
        if loser.breed == "Farmer":
            loser.die()
        elif loser.breed == "Hunter":
            loser.size *= loss
            loser.move_to()
        else:
            raise TypeError("Agent must be Farmer or Hunter.")

    def compete(self, other: SiteGroup) -> bool:
        """与其它主体竞争
        other: 竞争者
        return: True or False，竞争成功或失败
        """
        power = self.size * self.params.intensified_coefficient
        if (
            other.breed == "Farmer"
            and power >= other.size
            or other.breed != "Farmer"
            and other.breed == "Hunter"
            and self.size >= other.size
        ):
            self._loss_competition(other)
            return True
        if other.breed not in ["Farmer", "Hunter"]:
            raise TypeError("Agent must be Farmer or Hunter.")
        self._loss_competition(self)
        return False

    def able_to_go(self, cell: PatchCell) -> None:
        """狩猎采集者哪里都可以去"""
        if not isinstance(cell, PatchCell):
            raise TypeError(
                f"Agent must be put on a PatchCell, instead of {type(cell)}"
            )
        return True
