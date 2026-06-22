from dataclasses import dataclass


@dataclass(frozen=True)
class TopicPreset:
    name: str
    subject_hint: str
    ratio: str
    negative: str


TOPICS: dict[str, TopicPreset] = {
    "portrait": TopicPreset(
        "人像摄影",
        "专业人像摄影，面部自然，神态清晰，服饰精致，肤色真实，背景干净，细节丰富，高清质感",
        "3:4",
        "畸形手指，多余手指，手部错误，脸部扭曲，眼睛不对称，皮肤过度磨皮，模糊，低清晰度，水印，乱码文字",
    ),
    "character": TopicPreset(
        "游戏角色",
        "游戏角色设定，全身立绘，轮廓清晰，服装层次丰富，道具明确，材质细节，角色比例协调，高质量原画",
        "3:4",
        "肢体错位，多余肢体，手指融合，武器变形，服装杂乱，脸部崩坏，模糊，低质量，水印，乱码文字",
    ),
    "product": TopicPreset(
        "产品海报",
        "商业产品海报，主体突出，构图干净，高级材质，柔和反光，品牌质感，背景简洁，高清广告摄影",
        "1:1",
        "文字错误，水印，标志变形，重复产品，瓶身变形，反光错误，背景杂乱，模糊，低清晰度",
    ),
    "architecture": TopicPreset(
        "建筑空间",
        "建筑空间可视化，透视准确，空间层次清楚，材质真实，光线自然，家具比例协调，室内摄影质感",
        "16:9",
        "透视错误，结构变形，家具悬浮，窗户错位，空间混乱，布局杂乱，模糊，低质量",
    ),
    "chinese": TopicPreset(
        "国风美学",
        "新中式美学，东方意境，文化细节，雅致配色，柔和光影，留白构图，精致纹样，诗意氛围",
        "3:4",
        "现代杂物，服饰混乱，手部错误，建筑结构错误，装饰杂乱，文字乱码，水印，模糊，低质量",
    ),
    "scifi": TopicPreset(
        "科幻场景",
        "科幻概念设计，未来感结构，电影级光影，空间尺度宏大，机械细节清晰，霓虹氛围，高清场景原画",
        "16:9",
        "机械结构混乱，透视崩坏，噪点过多，细节糊成一片，比例错误，模糊，低质量，水印，乱码文字",
    ),
    "poster": TopicPreset(
        "电影海报",
        "电影海报构图，主体叙事明确，标题留白区域，强烈视觉焦点，戏剧化光影，宣传物料质感",
        "2:3",
        "文字乱码，错误字幕，构图拥挤，主体不清，脸部变形，低清晰度，水印，过度噪点",
    ),
    "illustration": TopicPreset(
        "插画场景",
        "完整插画场景，故事感明确，角色与环境关系清楚，色彩统一，画面层次丰富，细节耐看",
        "4:3",
        "线条杂乱，角色崩坏，透视混乱，色彩脏，低质量，模糊，水印，乱码文字",
    ),
    "storybook": TopicPreset(
        "儿童绘本",
        "儿童绘本画面，温暖友好，角色可爱，色彩柔和，叙事清楚，安全舒适，纸张绘本质感",
        "4:3",
        "恐怖氛围，表情诡异，肢体错误，低质量，模糊，文字乱码，水印，过度复杂背景",
    ),
    "logo": TopicPreset(
        "Logo图标",
        "标志图形设计，轮廓简洁，识别度高，中心构图，矢量感，清晰边缘，适合品牌视觉",
        "1:1",
        "复杂背景，文字乱码，边缘毛糙，图形变形，多余元素，低清晰度，水印，照片质感",
    ),
    "food": TopicPreset(
        "美食摄影",
        "专业美食摄影，食材新鲜，质感诱人，光线柔和，摆盘干净，浅景深，商业餐饮质感",
        "4:3",
        "食物变形，脏乱桌面，过曝，欠曝，模糊，低清晰度，水印，错误文字，异物感",
    ),
    "fashion": TopicPreset(
        "时装大片",
        "时装杂志大片，服装廓形明确，姿态优雅，布料材质清晰，妆发精致，摄影棚质感",
        "3:4",
        "身体比例错误，手部错误，服装破碎，脸部扭曲，过度磨皮，模糊，水印，低质量",
    ),
    "landscape": TopicPreset(
        "自然风景",
        "自然风景摄影，空间层次深远，光影自然，空气感，色彩真实，地貌清晰，高清旅行摄影",
        "16:9",
        "地平线扭曲，天空噪点，细节糊，过度锐化，过饱和，模糊，低清晰度，水印",
    ),
    "ecommerce": TopicPreset(
        "电商主图",
        "电商商品主图，产品居中，背景干净，卖点突出，材质清晰，光线均匀，高转化商业图",
        "1:1",
        "文字乱码，产品变形，重复产品，背景杂乱，阴影错误，低清晰度，模糊，水印",
    ),
    "wallpaper": TopicPreset(
        "壁纸封面",
        "高清壁纸画面，视觉中心明确，纵深感，色彩舒适，适合屏幕展示，干净耐看，氛围统一",
        "9:16",
        "主体裁切错误，噪点过多，过度复杂，模糊，低清晰度，水印，文字乱码",
    ),
}

STYLE_MAP: dict[str, str] = {
    "cinematic": "电影感，戏剧化构图，氛围光，景深，胶片质感，情绪张力",
    "editorial": "杂志编辑风，画面克制，排版感，高级留白，视觉秩序，精致完成度",
    "anime": "高质量动画插画，线条干净，色彩明确，细节刻画，角色表现力强",
    "realistic": "真实写实，自然光线，真实材质，细节准确，摄影级质感",
    "minimal": "极简构图，背景干净，色彩克制，主体明确，细节精准",
    "luxury": "高级奢华，精致材质，柔和高光，优雅构图，品牌大片质感",
    "ink": "水墨国风，墨色层次，留白构图，纸张肌理，东方韵味",
    "watercolor": "水彩质感，透明色层，柔和边缘，纸面纹理，轻盈氛围",
    "oil": "油画笔触，厚涂质感，色彩层次，经典绘画光影，艺术收藏感",
    "cyberpunk": "赛博朋克，霓虹灯光，雨夜反射，高对比色彩，未来都市氛围",
    "solarpunk": "太阳能朋克，自然科技融合，明亮绿植，生态建筑，乐观未来感",
    "isometric": "等距视角，结构清晰，小型世界，模块化细节，干净几何构图",
    "clay": "黏土渲染，柔软材质，圆润造型，微缩模型感，温和灯光",
    "pixel": "像素艺术，低分辨率格子美学，清晰轮廓，复古游戏质感",
    "three_d": "三维渲染，真实材质，体积光，干净模型，细节清晰，产品级渲染",
    "noir": "黑色电影，强烈明暗对比，低调光，悬疑气氛，深色阴影",
    "vaporwave": "蒸汽波，复古数字美学，粉蓝色调，网格空间，梦幻霓虹",
    "documentary": "纪实摄影，自然瞬间，真实场景，环境叙事，克制色彩",
}

STYLE_NAMES = {
    "cinematic": "电影感",
    "editorial": "杂志编辑",
    "anime": "高质动画",
    "realistic": "真实写实",
    "minimal": "极简干净",
    "luxury": "高级奢华",
    "ink": "水墨国风",
    "watercolor": "水彩质感",
    "oil": "油画厚涂",
    "cyberpunk": "赛博朋克",
    "solarpunk": "太阳能朋克",
    "isometric": "等距视角",
    "clay": "黏土渲染",
    "pixel": "像素艺术",
    "three_d": "三维渲染",
    "noir": "黑色电影",
    "vaporwave": "蒸汽波",
    "documentary": "纪实摄影",
}


def get_topic_options() -> list[dict[str, str]]:
    return [{"id": key, "name": preset.name, "ratio": preset.ratio} for key, preset in TOPICS.items()]


def get_style_options() -> list[dict[str, str]]:
    return [{"id": key, "name": STYLE_NAMES[key]} for key in STYLE_MAP]


def compose_prompt(topic: str, style: str, idea: str = "") -> dict[str, str]:
    preset = TOPICS.get(topic, TOPICS["scifi"])
    style_text = STYLE_MAP.get(style, STYLE_MAP["cinematic"])
    prompt = f"{preset.subject_hint}，{style_text}"
    return {
        "prompt": prompt,
        "negative_prompt": preset.negative,
        "ratio": preset.ratio,
    }
