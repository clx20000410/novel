"""
情绪曲线算法服务

根据章节在整本书中的位置，动态计算目标情绪强度和节奏参数。
"""
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import math


class ArcType(str, Enum):
    """故事弧线类型"""
    STANDARD = "standard"  # 标准三幕式
    SLOW_BURN = "slow_burn"  # 慢热型
    FAST_PACED = "fast_paced"  # 快节奏
    EPISODIC = "episodic"  # 单元剧式
    RISING = "rising"  # 持续上升
    WAVE = "wave"  # 波浪式


class EmotionCurveService:
    """情绪曲线算法服务"""

    # 标准情绪曲线定义（位置 -> 情绪强度范围）
    STANDARD_CURVE = {
        (0.00, 0.10): (30, 50, "铺垫期"),      # 前 10%：铺垫
        (0.10, 0.25): (50, 70, "上升期"),      # 10-25%：上升
        (0.25, 0.35): (70, 90, "第一高潮"),    # 25-35%：第一高潮
        (0.35, 0.50): (50, 70, "发展期"),      # 35-50%：发展
        (0.50, 0.60): (40, 60, "低谷期"),      # 50-60%：低谷
        (0.60, 0.75): (60, 80, "反转期"),      # 60-75%：反转
        (0.75, 0.90): (75, 95, "最终上升"),    # 75-90%：最终上升
        (0.90, 1.00): (85, 100, "大高潮"),     # 90-100%：大高潮
    }

    # 慢热型曲线
    SLOW_BURN_CURVE = {
        (0.00, 0.20): (20, 40, "慢铺垫"),
        (0.20, 0.40): (40, 55, "缓上升"),
        (0.40, 0.60): (55, 70, "稳定发展"),
        (0.60, 0.80): (65, 85, "加速期"),
        (0.80, 1.00): (80, 100, "爆发期"),
    }

    # 快节奏曲线
    FAST_PACED_CURVE = {
        (0.00, 0.05): (50, 65, "快速开场"),
        (0.05, 0.20): (65, 85, "第一波"),
        (0.20, 0.35): (55, 70, "短暂喘息"),
        (0.35, 0.50): (70, 90, "第二波"),
        (0.50, 0.65): (60, 75, "转折"),
        (0.65, 0.80): (75, 95, "第三波"),
        (0.80, 1.00): (85, 100, "终极高潮"),
    }

    # 波浪式曲线（适合长篇）
    WAVE_CURVE = {
        (0.00, 0.10): (30, 50, "开篇"),
        (0.10, 0.20): (60, 80, "小高潮1"),
        (0.20, 0.30): (40, 55, "回落1"),
        (0.30, 0.40): (65, 85, "小高潮2"),
        (0.40, 0.50): (45, 60, "回落2"),
        (0.50, 0.60): (70, 90, "中期高潮"),
        (0.60, 0.70): (50, 65, "回落3"),
        (0.70, 0.80): (75, 92, "小高潮3"),
        (0.80, 0.90): (55, 70, "最后回落"),
        (0.90, 1.00): (85, 100, "终极高潮"),
    }

    CURVES = {
        ArcType.STANDARD: STANDARD_CURVE,
        ArcType.SLOW_BURN: SLOW_BURN_CURVE,
        ArcType.FAST_PACED: FAST_PACED_CURVE,
        ArcType.WAVE: WAVE_CURVE,
    }

    def calculate_emotion_target(
        self,
        chapter_number: int,
        total_chapters: int,
        arc_type: ArcType = ArcType.STANDARD,
        volume_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        计算本章的目标情绪参数
        
        Args:
            chapter_number: 当前章节号
            total_chapters: 总章节数
            arc_type: 故事弧线类型
            volume_info: 分卷信息（如果有）
        
        Returns:
            包含情绪目标和节奏参数的字典
        """
        # 计算位置
        position = chapter_number / total_chapters if total_chapters > 0 else 0.5
        
        # 如果有分卷信息，考虑卷内位置
        if volume_info:
            volume_position = self._calculate_volume_position(chapter_number, volume_info)
            # 混合全局位置和卷内位置
            position = 0.6 * position + 0.4 * volume_position
        
        # 获取曲线
        curve = self.CURVES.get(arc_type, self.STANDARD_CURVE)
        
        # 查找对应区间
        emotion_min, emotion_max, phase_name = self._find_curve_segment(position, curve)
        
        # 计算精确的情绪强度（在区间内插值）
        emotion_target = self._interpolate_emotion(position, curve)
        
        # 计算节奏参数
        pacing = self._calculate_pacing(emotion_target, phase_name)
        
        # 计算爽点密度
        thrill_density = self._calculate_thrill_density(emotion_target, phase_name)
        
        # 计算对话/描写比例
        dialogue_ratio = self._calculate_dialogue_ratio(emotion_target, phase_name)
        
        return {
            "chapter_number": chapter_number,
            "position": round(position, 3),
            "phase_name": phase_name,
            "emotion_target": round(emotion_target, 1),
            "emotion_range": (emotion_min, emotion_max),
            "pacing": pacing,
            "thrill_density": thrill_density,
            "dialogue_ratio": dialogue_ratio,
            "recommendations": self._generate_recommendations(phase_name, emotion_target)
        }

    def _calculate_volume_position(
        self, 
        chapter_number: int, 
        volume_info: Dict[str, Any]
    ) -> float:
        """计算卷内位置"""
        volume_start = volume_info.get("start_chapter", 1)
        volume_end = volume_info.get("end_chapter", chapter_number)
        volume_length = volume_end - volume_start + 1
        
        if volume_length <= 0:
            return 0.5
        
        return (chapter_number - volume_start) / volume_length

    def _find_curve_segment(
        self, 
        position: float, 
        curve: Dict[Tuple[float, float], Tuple[int, int, str]]
    ) -> Tuple[int, int, str]:
        """查找位置对应的曲线区间"""
        for (start, end), (emotion_min, emotion_max, phase_name) in curve.items():
            if start <= position < end:
                return emotion_min, emotion_max, phase_name
        
        # 默认返回最后一个区间
        last_segment = list(curve.values())[-1]
        return last_segment

    def _interpolate_emotion(
        self, 
        position: float, 
        curve: Dict[Tuple[float, float], Tuple[int, int, str]]
    ) -> float:
        """在曲线上插值计算精确的情绪强度"""
        for (start, end), (emotion_min, emotion_max, _) in curve.items():
            if start <= position < end:
                # 在区间内线性插值
                segment_position = (position - start) / (end - start)
                return emotion_min + segment_position * (emotion_max - emotion_min)
        
        # 默认返回最后一个区间的最大值
        return list(curve.values())[-1][1]

    def _calculate_pacing(self, emotion_target: float, phase_name: str) -> Dict[str, Any]:
        """计算节奏参数"""
        # 情绪强度越高，节奏越快
        base_speed = emotion_target / 100
        
        # 根据阶段调整
        phase_modifiers = {
            "铺垫期": 0.7,
            "慢铺垫": 0.6,
            "上升期": 0.85,
            "缓上升": 0.75,
            "第一高潮": 1.1,
            "发展期": 0.8,
            "稳定发展": 0.8,
            "低谷期": 0.65,
            "反转期": 0.95,
            "加速期": 1.0,
            "最终上升": 1.05,
            "大高潮": 1.2,
            "爆发期": 1.15,
            "终极高潮": 1.2,
        }
        
        modifier = phase_modifiers.get(phase_name, 1.0)
        speed = min(1.0, base_speed * modifier)
        
        return {
            "speed": round(speed, 2),  # 0-1，越高越快
            "scene_length": "short" if speed > 0.8 else ("medium" if speed > 0.5 else "long"),
            "transition_style": "quick" if speed > 0.7 else ("smooth" if speed > 0.4 else "detailed"),
            "action_density": round(speed * 100)  # 动作密度百分比
        }

    def _calculate_thrill_density(self, emotion_target: float, phase_name: str) -> Dict[str, Any]:
        """计算爽点密度"""
        # 基础爽点数量（每章）
        base_thrills = emotion_target / 25  # 0-4 个爽点
        
        # 高潮期增加爽点
        if "高潮" in phase_name or "爆发" in phase_name:
            base_thrills *= 1.5
        elif "低谷" in phase_name or "回落" in phase_name:
            base_thrills *= 0.6
        
        return {
            "target_count": max(1, round(base_thrills)),
            "intensity": "high" if emotion_target > 75 else ("medium" if emotion_target > 50 else "low"),
            "spacing": "dense" if base_thrills > 3 else ("moderate" if base_thrills > 1.5 else "sparse")
        }

    def _calculate_dialogue_ratio(self, emotion_target: float, phase_name: str) -> Dict[str, Any]:
        """计算对话/描写比例"""
        # 高情绪强度 -> 更多对话和动作
        # 低情绪强度 -> 更多描写和内心戏
        
        if emotion_target > 75:
            dialogue_pct = 50
            action_pct = 30
            description_pct = 15
            inner_pct = 5
        elif emotion_target > 50:
            dialogue_pct = 40
            action_pct = 25
            description_pct = 20
            inner_pct = 15
        else:
            dialogue_pct = 30
            action_pct = 15
            description_pct = 30
            inner_pct = 25
        
        # 根据阶段微调
        if "铺垫" in phase_name:
            description_pct += 10
            dialogue_pct -= 10
        elif "高潮" in phase_name:
            action_pct += 10
            inner_pct -= 10
        
        return {
            "dialogue": dialogue_pct,
            "action": action_pct,
            "description": description_pct,
            "inner_monologue": inner_pct
        }

    def _generate_recommendations(self, phase_name: str, emotion_target: float) -> List[str]:
        """生成写作建议"""
        recommendations = []
        
        # 基于阶段的建议
        phase_recommendations = {
            "铺垫期": [
                "重点塑造角色，让读者产生代入感",
                "埋设伏笔，为后续剧情做铺垫",
                "不要急于推进主线，先建立世界观"
            ],
            "慢铺垫": [
                "细腻描写日常，展现角色性格",
                "通过小事件暗示未来冲突",
                "让读者充分了解主角的处境"
            ],
            "上升期": [
                "开始引入冲突，但不要一次性爆发",
                "让主角开始面对挑战",
                "适当增加悬念"
            ],
            "第一高潮": [
                "释放前期铺垫的张力",
                "让主角取得阶段性胜利或遭遇重大挫折",
                "这是留住读者的关键章节"
            ],
            "发展期": [
                "深化角色关系",
                "引入新的挑战或敌人",
                "推进支线剧情"
            ],
            "低谷期": [
                "让主角反思和成长",
                "可以安排一些温馨或日常的场景",
                "为下一波高潮蓄力"
            ],
            "反转期": [
                "揭示之前埋下的伏笔",
                "剧情出现重大转折",
                "打破读者的预期"
            ],
            "最终上升": [
                "所有线索开始汇聚",
                "主角做出关键决定",
                "营造紧迫感"
            ],
            "大高潮": [
                "全力释放情绪",
                "解决核心冲突",
                "给读者最大的满足感"
            ],
            "终极高潮": [
                "这是全书最精彩的部分",
                "所有伏笔在此揭晓",
                "让读者感到震撼和满足"
            ],
        }
        
        recommendations.extend(phase_recommendations.get(phase_name, []))
        
        # 基于情绪强度的建议
        if emotion_target > 80:
            recommendations.append("保持高强度的冲突和对抗")
            recommendations.append("对话要简短有力，动作要干脆利落")
        elif emotion_target < 40:
            recommendations.append("可以放慢节奏，多写内心戏")
            recommendations.append("适合处理角色关系和情感线")
        
        return recommendations[:5]  # 最多返回 5 条建议

    def get_chapter_macro_beat(
        self,
        chapter_number: int,
        total_chapters: int,
        arc_type: ArcType = ArcType.STANDARD
    ) -> str:
        """
        获取本章的 macro_beat（1234 节拍）
        
        基于情绪曲线动态分配，而不是简单的 chapter_number % 4
        """
        emotion_data = self.calculate_emotion_target(chapter_number, total_chapters, arc_type)
        phase_name = emotion_data["phase_name"]
        emotion_target = emotion_data["emotion_target"]
        
        # 根据阶段和情绪强度分配 macro_beat
        if "铺垫" in phase_name or emotion_target < 40:
            # 低情绪期：多用 E（事件）和 F（势力）
            return "E" if chapter_number % 2 == 1 else "F"
        elif "高潮" in phase_name or emotion_target > 75:
            # 高潮期：多用 P（挑衅）和 C（反击）
            return "P" if chapter_number % 2 == 1 else "C"
        else:
            # 中等情绪期：正常 1234 循环
            beats = ["E", "F", "P", "C"]
            return beats[chapter_number % 4]

    def get_emotion_curve_context(
        self,
        chapter_number: int,
        total_chapters: int,
        arc_type: ArcType = ArcType.STANDARD
    ) -> str:
        """生成情绪曲线上下文（用于注入到写作提示词）"""
        data = self.calculate_emotion_target(chapter_number, total_chapters, arc_type)
        
        lines = [
            "# 情绪曲线指导\n",
            f"## 当前位置：第 {chapter_number}/{total_chapters} 章（{data['position']*100:.1f}%）",
            f"## 阶段：{data['phase_name']}",
            f"## 目标情绪强度：{data['emotion_target']}/100",
            "",
            "## 节奏参数",
            f"- 节奏速度：{data['pacing']['speed']} ({data['pacing']['scene_length']})",
            f"- 场景长度：{data['pacing']['scene_length']}",
            f"- 过渡风格：{data['pacing']['transition_style']}",
            "",
            "## 爽点密度",
            f"- 目标数量：{data['thrill_density']['target_count']} 个/章",
            f"- 强度：{data['thrill_density']['intensity']}",
            "",
            "## 内容比例建议",
            f"- 对话：{data['dialogue_ratio']['dialogue']}%",
            f"- 动作：{data['dialogue_ratio']['action']}%",
            f"- 描写：{data['dialogue_ratio']['description']}%",
            f"- 内心戏：{data['dialogue_ratio']['inner_monologue']}%",
            "",
            "## 写作建议",
        ]
        
        for rec in data["recommendations"]:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
