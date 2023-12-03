#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from pathlib import Path

import pandas as pd
import seaborn as sns
from abses import ActorsList, MainModel
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from .env import Env


class Model(MainModel):
    """运行的模型"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, nature_class=Env, **kwargs)
        self.nature.add_hunters()
        self.farmers_num = []
        self.new_farmers = []
        self.hunters_num = []
        self.outpath = kwargs.get("outpath")

    @property
    def outpath(self) -> str:
        """输出文件夹"""
        return self._path

    @outpath.setter
    def outpath(self, path: str) -> None:
        """设置输出文件夹"""
        path_obj = Path(path)
        if not path_obj.is_dir():
            raise FileExistsError(f"{path} not exist.")
        self._path = path_obj

    @property
    def farmers(self) -> ActorsList:
        """农民列表"""
        return self.agents.select("Farmer")

    @property
    def hunters(self) -> ActorsList:
        """狩猎采集者列表"""
        return self.agents.select("Hunter")

    def trigger(self, actors: ActorsList, func: str, *args, **kwargs) -> None:
        """触发所有还活着的主体的行动"""
        for actor in actors:
            if not actor.on_earth:
                continue
            getattr(actor, func)(*args, **kwargs)

    def step(self):
        """每一时间步都按照以下顺序执行一次：
        1. 更新农民数量
        2. 所有主体互相转化
        3. 更新狩猎采集者可以移动（这可能触发竞争）
        """
        farmers = self.nature.add_farmers()
        self.trigger(self.actors, "population_growth")
        self.trigger(self.actors, "convert")
        self.trigger(self.actors, "diffuse")
        self.trigger(self.hunters, "move")
        # 更新农民和狩猎采集者数量
        self.new_farmers.append(len(farmers))
        self.farmers_num.append(self.farmers.array("size").sum())
        self.hunters_num.append(self.hunters.array("size").sum())

    @property
    def dataset(self) -> pd.DataFrame:
        """数据"""
        data = {
            "new_farmers": self.new_farmers,
            "farmers_num": self.farmers_num,
            "hunters_num": self.hunters_num,
        }
        return pd.DataFrame(data=data, index=range(self.time.tick))

    def export_data(self) -> None:
        """导出实验数据"""
        self.dataset.to_csv(self.outpath / f"repeat_{self.run_id}.csv")

    def end(self):
        """模型运行结束后，将自动绘制狩猎采集者和农民的数量变化"""
        save_fig = self.params.get("save_plots")
        self.plot(save=save_fig)
        self.heatmap(save=save_fig)
        self.plot_histplots(save=save_fig)
        self.export_data()

    def plot(self, save: bool = False) -> Axes:
        """绘制狩猎采集者和农民的数量变化"""
        _, ax = plt.subplots()
        ax.plot(self.farmers_num, label="farmers")
        ax.plot(self.hunters_num, label="hunters")
        ax.set_xlabel("time")
        ax.set_ylabel("population")
        ax.legend()
        if save:
            plt.savefig(self.outpath / f"repeat_{self.run_id}_plot.jpg")
            plt.close()
        return ax

    def heatmap(self, save: bool = False):
        """绘制狩猎采集者和农民的空间分布"""
        _, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
        mask = self.nature.dem.get_xarray("elevation") >= 0
        farmers = self.nature.dem.get_xarray("farmers").where(mask)
        hunters = self.nature.dem.get_xarray("hunters").where(mask)
        farmers.plot.contourf(ax=ax1, cmap="Reds")
        hunters.plot.contourf(ax=ax2, cmap="Greens")
        ax1.set_xlabel("Farmers")
        ax2.set_xlabel("Hunters")
        if save:
            plt.savefig(self.outpath / f"repeat_{self.run_id}_heatmap.jpg")
            plt.close()
        return ax1, ax2

    def plot_histplots(self, save: bool = False):
        _, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
        sns.histplot(self.farmers.array("size"), ax=ax1)
        sns.histplot(self.hunters.array("size"), ax=ax2)
        ax1.set_xlabel("Farmers")
        ax2.set_xlabel("Hunters")
        if save:
            plt.savefig(self.outpath / f"repeat_{self.run_id}_histplot.jpg")
            plt.close()
        return ax1, ax2
