# 国际化（i18n）模块
# 提供翻译函数 t()，根据当前语言设置返回对应文本
# 支持中文/英文切换，运行时动态加载翻译字典
from config.i18n.zh_cn import TRANSLATIONS as ZH_CN
from config.i18n.en_us import TRANSLATIONS as EN_US
from config.settings import get_language, load_user_config, save_user_config

_TRANSLATIONS = {
    "zh_cn": ZH_CN,
    "en_us": EN_US,
}

_current_lang = get_language()


def set_language(lang: str):
    global _current_lang
    _current_lang = lang
    config = load_user_config()
    config["language"] = lang
    save_user_config(config)


def get_current_language():
    return _current_lang


def t(key: str) -> str:
    translations = _TRANSLATIONS.get(_current_lang, ZH_CN)
    return translations.get(key, key)
