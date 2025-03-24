import os
import sys
from time import time
from datetime import datetime
import re
import pandas as pd
import requests
import zhconv
import openpyxl
from comtypes.client import CreateObject
import win32gui
from difflib import SequenceMatcher
import math


def cm_to_points(cm):
    return (cm * 72) / 2.54


SETTING_SHEET = '全局设置'
LIST_SHEET = '各歌设置'
EXCLUDED_ROLES = [
    '编曲',
    '制作人',
    '监制',
    'OP',
    'SP',
    '和音',
    '录音',
    '混音',
    'Mastering',
    '编程',
    '键盘',
    '吉他',
    '电吉他',
    '电结他',
    '贝斯',
    '鼓',
    '弦乐编写',
    '铜管乐编写',
    '和声编写',
    '和声',
    '混音师',
    '录音室',
    '混音室',
    '录音工程师',
    '母带后期处理录音师',
    '录音室',
    '母带后期处理录音室',
    '基本轨录音工程',
    '演唱',
    '主唱',
]
DEFAULT_SINGER = '默'
CHORUS_SINGER = '合'
TIME_LYRIC_SPLITTER = ']'
SINGER_LYRIC_SPLITTERS = ['：', ':']
SINGER_LYRIC_SPLITTER_PATTERN = '|'.join(map(re.escape, SINGER_LYRIC_SPLITTERS))  # 将分隔符数组转换为正则表达式
MULTIPLE_SINGER_SPLITTER = '___'
SHOW_LEN_2_PTS = {
    0: {
        'font': 54,
        'line': 72,
    },
    22: {
        'font': 45,
        'line': 60,
    },
    30: {
        'font': 39,
        'line': 52,
    },
    38: {
        'font': 32,
        'line': 36,
    },
}
PADDING_TOP = cm_to_points(0)
IS_COVER_ONLY = False
IS_DYNAMIC_LYRIC = True
IS_TRADITIONAL = False
MAX_FONT_SIZE_PT = 54
LINE_SPACING = 16


def get_song_info(sid):
    search_url = f'https://yinyue.kuwo.cn/openapi/v1/www/lyric/getlyric?musicId={sid}'
    response = requests.get(search_url)
    return response.json()


def is_chinese(char):
    # 判断字符的Unicode是否在中文字符的范围内
    if '\u4e00' <= char <= '\u9fff':
        return True
    return False


def is_all_not_chinese(chars):
    return not any(is_chinese(c) for c in chars)


def time_to_seconds(time_str):
    # 将时间字符串分割成分钟、秒和毫秒部分
    minutes, rest = time_str.split(':')
    seconds, milliseconds = rest.split('.')

    # 转换为秒
    total_seconds = int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds


def extract_song(lyrics):
    song_info = {}
    song_info['lyrics'] = []
    # 分析歌词列表
    for lyric in lyrics:
        line_lyric = lyric['lineLyric']

        if ' - ' in line_lyric:
            song_info['songName'] = line_lyric.split(' - ')[0]
        else:
            words = re.split(SINGER_LYRIC_SPLITTER_PATTERN, line_lyric)
            if len(words) > 1:
                if any(role in words[0].split(' ')[0].strip() for role in EXCLUDED_ROLES):
                    continue

                if line_lyric.find('词') != -1:
                    song_info['lyricist'] = words[1]
                    continue
                elif line_lyric.find('曲') != -1:
                    song_info['composer'] = words[1]
                    continue

    return song_info


def get_pts(show_len):
    font_pt = line_pt = 0
    for key in SHOW_LEN_2_PTS.keys():
        if key > show_len:
            break

        obj = SHOW_LEN_2_PTS[key]
        font_pt = obj['font']
        line_pt = obj['line']

    return font_pt, line_pt


def get_from_163(artist_name, song_name):
    url = "https://music.163.com/api/search/get/web"
    query = f'{artist_name} "{song_name}"'
    params = {
        "csrf_token": "",
        "s": query,
        "type": 1,  # 1 表示搜索歌曲
        "offset": 0,
        "limit": 5  # 返回前 5 条结果
    }

    response = requests.get(url, params=params)
    return response.json()


def get_dynamic_lyrics(artist_name, song_name, change_lyrics, changed_lyrics, specified_163_id):
    def similarity_ratio(str1, str2):
        return SequenceMatcher(None, str1, str2).ratio()

    def match_song_artist(x):
        return similarity_ratio(x['name'], song_name) >= 0.4 and 'artists' in x and similarity_ratio(
            x['artists'][0]['name'], artist_name) >= 0.4

    def match_song(x):
        return similarity_ratio(x['name'], song_name) >= 0.1

    def is_valid_lyric(x):
        # Lambda 表达式，用于匹配格式 "[00:21xx]abc"
        pattern = r"^\[\d{2}:\d{2}.*\].+"
        return re.match(pattern, x)

    def replace_lyrics(arr, change_lyrics, changed_lyrics):
        # 替换某些古怪的歌词：如记忆棉最后一句“——-”
        result = []
        for item in arr:
            # 用']'分割字符串
            parts = item.split(TIME_LYRIC_SPLITTER)
            if len(parts) > 1:
                # 歌词会有些形如“[01:50.67][00:36.57]谁伴我 冒险跳下爱河”
                # 最后部分为歌词，把它的中文空格转为英文空格
                prefix, lyric = parts[0], parts[-1].replace("　", " ").strip()
                if any(role in re.split(SINGER_LYRIC_SPLITTER_PATTERN, lyric)[0].strip() for role in EXCLUDED_ROLES + ['作词', '作曲']):
                    # 排除形如 [00:05.0]编曲：Johnny Yim 的歌词
                    continue

                # 如果歌词在 change_lyrics 中，进行替换
                for i, change_lyric in enumerate(change_lyrics):
                    if similarity_ratio(change_lyric, lyric) >= 0.8:
                        lyric = changed_lyrics[i]
                        break

                for part in parts[:-1]:
                    result.append(f"{part}{TIME_LYRIC_SPLITTER}{lyric}")

            else:
                # 若无法分割，直接添加到结果数组
                result.append(item)

        # 把歌词根据时间排序
        return sorted(result)

    params = {
        "id": specified_163_id,
    }
    if not specified_163_id:
        # 只在有歌曲和歌手都匹配的结果里找最小的id
        res = get_from_163(artist_name, song_name)
        # 过滤没有时间的行
        songs = list(filter(match_song_artist, res['result']['songs']))
        if len(songs) == 0:
            # 如《遗物 - (TVB电视剧《法外风云》主题曲)》这种歌如果加上歌手会搜不到，所以减少歌手再找一次
            res = get_from_163('', song_name)
            songs = list(filter(match_song, res['result']['songs']))

        song = min(songs, key=lambda s: s['id'])
        params = {
            "id": song['id'],
        }

    url = 'http://music.163.com/api/song/media'
    response = requests.get(url, params=params)
    # 转换括号，修复一些typo
    lrc_str = response.json()['lyric'].replace('（(', '（').replace('（', '(').replace('）', ')').replace('\\u3000', ' ')
    tmp_lrcs = lrc_str.split('\n')
    lrcs = []
    for i, tmp_lrc in enumerate(tmp_lrcs):
        if is_valid_lyric(tmp_lrc):
            lrcs.append(tmp_lrc)
        elif tmp_lrc.strip() != '' and tmp_lrc.find('[') == -1:
            # 如果没有时间戳，添加
            lrcs.append(f'[00:00.{str(i).zfill(2)}]' + tmp_lrc)

    print(song_name, params, lrcs)

    # 过滤没有时间的行
    return replace_lyrics(list(filter(is_valid_lyric, lrcs)), change_lyrics, changed_lyrics)


# 检查字体是否在系统中可用
def is_font_available(font_name):
    # 回调函数，用于添加字体名称
    def enum_font_callback(logfont, textmetric, font_type, font_list):
        font_list.append(logfont.lfFaceName)
        return True

    # 获取系统中的字体
    def get_system_fonts():
        fonts = []
        # 使用 EnumFontFamilies 函数枚举字体
        hdc = win32gui.GetDC(0)  # 获取屏幕的设备上下文
        win32gui.EnumFontFamilies(hdc, None, enum_font_callback, fonts)
        win32gui.ReleaseDC(0, hdc)  # 释放设备上下文
        return sorted(set(fonts))  # 去重并排序

    # 检查字体名称是否在可用字体列表中
    return font_name in get_system_fonts()


def add_textbox(slide, shape, left, top, width, height, text, font_pt, solo_colors, chorus_color, cover_color, singers=None):
    def conv_chn(lyric):
        return zhconv.convert(lyric, 'zh-hk') if IS_TRADITIONAL else lyric

    # 定义 PowerPoint 对齐常量
    ppAlignLeft = 1
    ppAlignCenter = 2

    template_font = shape.TextFrame.TextRange.Font
    tb = slide.Shapes.AddTextbox(
        Orientation=1,  # msoTextOrientationHorizontal
        Left=left,
        Top=top,
        Width=width,
        Height=height,
    )
    tb.Rotation = shape.Rotation
    tf = tb.TextFrame
    # 中文空格转为英文空格
    strip_str = text.strip()
    is_song_name = False
    for i, _ in enumerate(strip_str.split('\n')):
        # 字体有可能本机没有装，要先从 https://freefonts.top/font/60a5feb12b07ed2b26d4e1dd 下载安装，否则打开文件选取文字时会改变字体
        # 检查字体是否可用
        # Font.Name设置的仅为拉丁字体，因此中文字符可能未受到影响
        # 要确保中文字体生效需要设置 Font.NameFarEast 属性
        if is_font_available(template_font.Name):
            tf.TextRange.Font.Name = template_font.Name
            tf.TextRange.Font.NameFarEast = template_font.Name
        else:
            tf.TextRange.Font.Name = "宋体"  # 使用默认字体
            tf.TextRange.Font.NameFarEast = "宋体"  # 使用默认字体

        tf.TextRange.Font.Size = font_pt
        tf.TextRange.Font.Bold = template_font.Bold
        tf.TextRange.Font.Italic = template_font.Italic
        tf.TextRange.Font.Underline = template_font.Underline
        # 转换中文简繁
        if singers is None:
            # 封面
            tf.TextRange.Text = conv_chn(strip_str)
            tf.TextRange.Font.Color.RGB = cover_color
        else:
            if strip_str.find(SINGER_LYRIC_SPLITTERS[0]) == -1:
                # 没有歌手，意味着是 歌名
                is_song_name = True
                if len(singers) == 0:
                    # 单个歌手，直接显示歌名
                    tf.TextRange.Text = conv_chn(strip_str)
                else:
                    # 多个歌手，本行是：歌名（歌手颜色：歌手1 歌手2。。） 这个格式，歌手1 2。。用不同颜色
                    pfx = f'{strip_str}（歌手及颜色：'
                    pos = len(pfx)
                    s = ''
                    for j, singer in enumerate(singers):
                        # +1意味着用空格隔开
                        l = len(singer) + 1
                        s += singer + ' '
                        pos += l

                    sfx = '合唱）'
                    s = pfx + s + sfx
                    tf.TextRange.Text = conv_chn(s)
                    pos = len(pfx) + 1
                    for j, singer in enumerate(singers):
                        l = len(singer)
                        chars = tf.TextRange.Characters(pos, l)
                        chars.Font.Color.RGB = solo_colors[j]
                        # +1意味着用空格隔开
                        pos += l + 1

                    chars = tf.TextRange.Characters(pos, 2)
                    chars.Font.Color.RGB = chorus_color

            else:
                # 有歌手，意味着是 歌词
                words = strip_str.split(MULTIPLE_SINGER_SPLITTER)
                ws = []
                for word in words:
                    [_, lyric] = re.split(SINGER_LYRIC_SPLITTER_PATTERN, word)
                    s = conv_chn(lyric)
                    ws.append(s)

                tf.TextRange.Text = ' '.join(ws)

                pos = 1
                for word in words:
                    [singer, lyric] = re.split(SINGER_LYRIC_SPLITTER_PATTERN, word)
                    if singer == DEFAULT_SINGER:
                        tf.TextRange.Font.Color.RGB = solo_colors[0]
                    else:
                        chars = tf.TextRange.Characters(pos, len(lyric))
                        try:
                            idx = singers.index(singer)
                            # 找得到歌手，意味着不是合唱
                            chars.Font.Color.RGB = solo_colors[idx]
                        except Exception:
                            # 找不到歌手，意味着是合唱
                            chars.Font.Color.RGB = chorus_color

                    # 要用空格连起来，所以+1
                    pos += len(lyric) + 1

        source_alignment = shape.TextFrame.TextRange.ParagraphFormat.Alignment
        if IS_DYNAMIC_LYRIC:
            tf.TextRange.ParagraphFormat.Alignment = source_alignment
        else:
            tf.TextRange.ParagraphFormat.Alignment = ppAlignCenter if is_song_name else ppAlignLeft

    return tb


def add_animation(slide, idx, shapes, distance, formatted_lyrics):
    msoAnimTriggerOnPageClick = 1
    msoAnimTriggerAfterPrevious = 3
    msoAnimEffectPathUp = 148
    msoAnimTypeNone = 0
    msoAnimTypeMotion = 1
    # 要分别用 msoAnimOpacity 和 msoAnimVisibility 控制显示/隐藏
    msoAnimTypeProperty = 5
    msoAnimOpacity = 5
    msoAnimVisibility = 8
    msoAnimShapeFillOpacity = 1006
    # 最顶的歌词，在上一动画后，显示歌词时长，然后消失
    effect = slide.TimeLine.MainSequence.AddEffect(
        shapes[0],
        effectId=msoAnimTypeNone,
        trigger=msoAnimTriggerAfterPrevious,
    )
    behavior = effect.Behaviors.Add(msoAnimTypeProperty)
    behavior.PropertyEffect.Property = msoAnimOpacity
    effect.Timing.Duration = (formatted_lyrics[idx + 1]['sec'] - formatted_lyrics[idx]['sec']) if idx <= len(formatted_lyrics) - 2 else 9999

    effect = slide.TimeLine.MainSequence.AddEffect(
        shapes[0],
        effectId=msoAnimTypeNone,
        # 第一行歌词，点击后才开始动画
        trigger=msoAnimTriggerOnPageClick if idx == 0 else msoAnimTriggerAfterPrevious,
    )
    behavior = effect.Behaviors.Add(msoAnimTypeProperty)
    behavior.PropertyEffect.Property = msoAnimVisibility
    effect.Timing.Duration = 0

    # 其他歌词，在上一动画后上移
    for shape in shapes[1:]:
        effect = slide.TimeLine.MainSequence.AddEffect(
            shape,
            effectId=msoAnimEffectPathUp,
            trigger=msoAnimTriggerAfterPrevious,
        )
        # 设置路径动画的属性——移动距离 = idx==0时的y到当前的y * 0.25，上移是负数
        behavior = effect.Behaviors.Add(msoAnimTypeMotion)
        behavior.MotionEffect.ByX = 0
        behavior.MotionEffect.ByY = -distance * (idx + 1) * 0.25
        effect.Timing.Duration = 0


def generate_ppt(new_ppt, row, row_idx):
    song_name = str(row['歌曲'])
    artist_name = str(row['歌手'])
    singer_cnt = row['歌手数量']
    cover_color = get_setting_color(file_path, LIST_SHEET, '封面字体颜色', row_idx + 2)
    chorus_color = get_setting_color(file_path, LIST_SHEET, '合唱歌词颜色', row_idx + 2)
    solo_colors = []
    change_lyrics = str(row['要修改的歌词']).split('\n')
    changed_lyrics = str(row['修改后歌词']).split('\n')
    specified_kuwo_id = str(int(row['指定酷我音乐歌曲ID'])) if not math.isnan(row['指定酷我音乐歌曲ID']) else ''
    specified_163_id = str(int(row['指定网易云歌曲ID'])) if not math.isnan(row['指定网易云歌曲ID']) else ''
    for i in list(range(singer_cnt)):
        solo_colors.append(get_setting_color(file_path, LIST_SHEET, f'歌手{i + 1}歌词颜色', row_idx + 2))

    # 搜索歌曲ID
    search_url = f'https://yinyue.kuwo.cn/search/searchMusicBykeyWord?vipver=1&client=kt&ft=music&cluster=0&strategy=2012&encoding=utf8&rformat=json&mobi=1&issubtitle=1&show_copyright_off=1&pn=0&rn=20&all={song_name} {artist_name}'
    response = requests.get(search_url)
    infos = response.json()['abslist']
    scores = []
    for i in range(0, min(5, len(infos))):
        score = 0
        sid = infos[i]['DC_TARGETID']
        if sid == specified_kuwo_id:
            # 匹配指定的酷我音乐id，直接使用该sid
            score = 99999
            scores.append(score)
            break

        song = get_song_info(sid)
        if 'lrclist' not in song['data']:
            # 没有歌词的，不采用
            score = -1
            scores.append(score)
            continue

        has_lyricist = False
        has_composer = False
        for item in song['data']['lrclist']:
            # 没有词曲的，不采用
            if item['lineLyric'].find('词') != -1:
                has_lyricist = True

            if item['lineLyric'].find('曲') != -1:
                has_composer = True

        if not has_lyricist or not has_composer:
            score = -1
            scores.append(score)
            continue

        # 符合以下条件的歌词，每符合一个条件加分：
        # 1. 歌手名匹配
        # 2. 歌名匹配
        # 3. 网站有MV
        arr1 = artist_name.upper().split('&')
        arr2 = infos[i]['FARTIST'].upper().split('&')
        if sorted(arr1) == sorted(arr2):
            score += 1

        file_song_name = song_name.strip().replace('（', '(').replace('）', ')').upper()
        web_song_name = infos[i]['SONGNAME'].strip().replace('（', '(').replace('）', ')').upper()
        if file_song_name == web_song_name:
            score += 1

        if infos[i]['MVFLAG'] == '1':
            score += 1

        scores.append(score)

    idx = scores.index(max(scores))
    sid = infos[idx]['DC_TARGETID']
    song = get_song_info(sid)
    # 把唱片封面改成700*700（酷我封面的最大值）
    album_cover = f"https://img1.kuwo.cn/star/albumcover/{infos[idx]['web_albumpic_short']}".replace('/120/', '/700/')
    response = requests.get(album_cover)
    # 保存图片到本地文件
    with open('tmp.jpg', 'wb') as file:
        file.write(response.content)

    if 'lrclist' in song['data']:
        song_info = extract_song(song['data']['lrclist'])
    else:
        song_info = {}

    slides, layout = get_last_layout(new_ppt)
    template_song_slide = slides[1]
    template_lyric_slide = slides[2]
    if IS_DYNAMIC_LYRIC:
        # 处理歌曲封面
        slide = slides.AddSlide(slides.Count + 1, layout)
        for shape in template_song_slide.shapes:
            # 获取图形的位置和大小
            left = shape.left
            top = shape.top
            width = shape.width
            height = shape.height
            if shape.HasTextFrame:  # msoTextBox
                text = shape.TextFrame.TextRange.Text
                if text.find('<歌名>') != -1:
                    text = text.replace('<歌名>', song_info['songName'] if 'songName' in song_info else '')
                if text.find('<歌手>') != -1:
                    text = text.replace('<歌手>', artist_name)
                if text.find('<作曲人>') != -1:
                    text = text.replace('<作曲人>', song_info['composer'] if 'composer' in song_info else '')
                if text.find('<作词人>') != -1:
                    text = text.replace('<作词人>', song_info['lyricist'] if 'lyricist' in song_info else '')

                add_textbox(slide, shape, left, top, width, height, text, shape.TextFrame.TextRange.Font.Size, solo_colors, chorus_color, cover_color)

            # 判断形状类型是否为 AutoShape 或 Picture
            elif shape.Type == 1:  # msoAutoShape
                # 添加一个新的 AutoShape 到幻灯片
                new_shape = slide.Shapes.AddShape(
                    1,  # msoShapeRectangle (示例形状)
                    Left=left,
                    Top=top,
                    Width=width,
                    Height=height,
                )
                new_shape.Fill.ForeColor.RGB = shape.Fill.ForeColor.RGB

            elif shape.Type == 13:  # msoPicture
                # 添加一个新的图片到幻灯片
                picture_path = f"{os.getcwd()}/tmp.jpg"  # 指定图片路径
                slide.Shapes.AddPicture(
                    picture_path,
                    LinkToFile=False,
                    SaveWithDocument=True,
                    Left=left,
                    Top=top,
                    Width=width,
                    Height=height,
                )

        if IS_COVER_ONLY:
            return new_ppt

    # 添加歌词
    lyrics = get_dynamic_lyrics(artist_name, song_name, change_lyrics, changed_lyrics, specified_163_id)
    # 检查并提取模板幻灯片中的文本框
    template_text_boxs = [shape for shape in template_lyric_slide.shapes if shape.HasTextFrame]
    # 找出占用最大字节数的元素
    max_len = 0
    longest_lyric = ''
    curr_singer = DEFAULT_SINGER
    singers = []
    formatted_lyrics = []
    is_move_time = False
    for i, lyric in enumerate(lyrics):
        words = lyric.split(TIME_LYRIC_SPLITTER)
        # 获取时间
        sec = time_to_seconds(words[0][1:])
        if i != 0:
            if not is_move_time:
                if 'trimmed_lyric' in formatted_lyrics[i - 1]:
                    prev_lyric = formatted_lyrics[i - 1]['trimmed_lyric']
                    prev_sec = formatted_lyrics[i - 1]['sec']
                    if (sec - prev_sec) < 2 and len(prev_lyric) > 6 and i < len(lyrics) - 1:
                        # 如果前一歌词时间<2s而且文字>6，意味着和本句是合唱，要同时出现和消失，所以要获取下一句的时间，作为本句的时间
                        is_move_time = True
                        ws = lyrics[i + 1].split(TIME_LYRIC_SPLITTER)
                        # 获取时间
                        sec = time_to_seconds(ws[0][1:])

            else:
                is_move_time = False
                sec = formatted_lyrics[i - 1]['sec']

        formatted_lyrics.append({'sec': sec})

        # 获取歌词，括号是合唱特征
        chn_colon = SINGER_LYRIC_SPLITTERS[0]
        ws = re.split(SINGER_LYRIC_SPLITTER_PATTERN, words[1])
        # 歌词如果已有2个冒号，不需再加；否则加1个冒号
        tw = chn_colon if len(ws) < 2 else ''
        if words[1].find('(') == 0:
            # 如果第一个字符是(，意味着这歌词用了`(歌手)歌词`的格式，来指明本句的歌手，要转换为：`歌手：歌词`这个格式
            strip_str = words[1].replace('(', '').replace(')', f'{chn_colon}')
        else:
            strip_str = words[1].replace(')', '').replace('(', f'{tw}(').replace('(', '')\
                .replace(f'{chn_colon}{chn_colon}', f'{chn_colon}')

        words = re.split(SINGER_LYRIC_SPLITTER_PATTERN, strip_str)
        if len(words) > 1:
            # 合唱歌曲
            # 如果歌手有&字符，视为合唱
            singer = words[0].strip() if words[0].find('&') == -1 else CHORUS_SINGER
            if singer == '合唱':
                singer = CHORUS_SINGER

            singer = zhconv.convert(singer, 'zh-cn')
            if curr_singer == DEFAULT_SINGER:
                curr_singer = singer

            singer_len = len(singer)
            if singer_len != len(curr_singer) and singer != CHORUS_SINGER:
                # 不正常的歌手简称，如：无非想 扮诚实来换舒畅P，其实这是"合唱，本行有2个歌手"这种情况
                words = f'{curr_singer}{chn_colon}{strip_str}'.split(chn_colon)
                singer = curr_singer
                singer_len = len(singer)

            if singer == CHORUS_SINGER:
                # 排除合唱的歌手：合
                formatted_lyrics[i]['singer_lyric'] = f'{CHORUS_SINGER}{chn_colon}{words[1]}'
                formatted_lyrics[i]['trimmed_lyric'] = words[1]
            else:
                if singer not in singers:
                    singers.append(singer)

                if singer != curr_singer:
                    curr_singer = singer

                if len(words) == 2:
                    # 合唱，本行是独唱
                    formatted_lyrics[i]['singer_lyric'] = f'{curr_singer}{chn_colon}{words[1]}'
                    formatted_lyrics[i]['trimmed_lyric'] = words[1]
                else:
                    # 合唱，本行有2个歌手，words[1]是第一个歌手的歌词+第二个歌手的简称
                    singer = words[1][-singer_len:]
                    if singer not in singers:
                        # 属于括号前没有歌手的情况，歌手为非 curr_singer 的那个歌手
                        idx = len(singers) - singers.index(curr_singer) - 1
                        singer = singers[idx]
                        words[1] += singer

                    tl = len(words[1])
                    w1 = words[1][:tl - singer_len]
                    w2 = words[2]
                    formatted_lyrics[i]['singer_lyric'] = f'{curr_singer}{chn_colon}{w1}{MULTIPLE_SINGER_SPLITTER}{singer}{chn_colon}{w2}'
                    formatted_lyrics[i]['trimmed_lyric'] = f'{w1} {w2}'

        else:
            # 独唱歌曲
            formatted_lyrics[i]['singer_lyric'] = f'{curr_singer}{chn_colon}{words[0]}'
            formatted_lyrics[i]['trimmed_lyric'] = words[0]

        ml = len(formatted_lyrics[i]['trimmed_lyric'].encode('utf-8'))
        if ml > max_len:
            max_len = ml
            longest_lyric = formatted_lyrics[i]['trimmed_lyric']

    max_show_len = 0
    for c in longest_lyric:
        delta = 2 if is_chinese(c) else 1
        max_show_len += delta

    font_pt, line_pt = get_pts(max_show_len)
    slide = slides.AddSlide(slides.Count + 1, layout)
    idx = left = 0
    lyric_width = new_ppt.PageSetup.SlideWidth
    top = PADDING_TOP
    is_all_eng = True
    for formatted_lyric in formatted_lyrics:
        if not is_all_not_chinese(formatted_lyric['trimmed_lyric']):
            # 不全是英文
            is_all_eng = False
            break

    tmp_font_pt = font_pt
    distance = line_pt + LINE_SPACING
    line_height_pt = distance + 4
    if not (IS_DYNAMIC_LYRIC or is_all_eng):
        # 动态歌词 或 全是英文，字体、行距不变，否则要改变
        tmp_font_pt = font_pt / 2
        distance = line_pt / 2 + LINE_SPACING
    elif is_all_eng:
        # 如果歌词全是英文，而且句子达到最长的级别，需要缩小字体
        tmp_font_pt = 24 if font_pt == 32 else font_pt

    if not IS_DYNAMIC_LYRIC:
        # 警惕歌词，歌词要上对齐，在增加textbox前就要设好ppt高度 和 加歌名
        new_ppt.PageSetup.SlideHeight = line_height_pt * len(formatted_lyrics)

        if not is_all_eng:
            # 如果有非英文，缩短slide高度
            new_ppt.PageSetup.SlideHeight /= 2.4

        add_textbox(slide, template_text_boxs[0], left, top, lyric_width, line_pt, song_name, tmp_font_pt, solo_colors,
                chorus_color, cover_color, singers)

    for i, formatted_lyric in enumerate(formatted_lyrics):
        if 'singer_lyric' in formatted_lyric:
            text = formatted_lyric['singer_lyric']
            if not IS_DYNAMIC_LYRIC:
                # 静态歌词：
                # 1、如果全句都是英文，独立一行显示
                # 2、否则一行显示两句歌词
                if is_all_not_chinese(formatted_lyric['trimmed_lyric']):
                    lyric_width = new_ppt.PageSetup.SlideWidth
                    top += distance
                    left = 0
                    idx = 0
                else:
                    lyric_width = new_ppt.PageSetup.SlideWidth / 2
                    if idx % 2 == 0:
                        top += distance
                        left = 0
                    else:
                        left = lyric_width

                    idx += 1

            else:
                top += distance

            add_textbox(slide, template_text_boxs[0], left, top, lyric_width, line_pt, text, tmp_font_pt, solo_colors, chorus_color, cover_color, singers)

    if not IS_DYNAMIC_LYRIC:
        return new_ppt

    text_boxs = [shape for shape in slide.shapes if shape.HasTextFrame]
    for i, _ in enumerate(text_boxs):
        add_animation(slide, i, text_boxs[i:], distance, formatted_lyrics)
        # if i == 2:
        #     break

    return new_ppt


def get_setting_color(file_path, sheet_name, col_name, row_no):
    workbook = openpyxl.load_workbook(file_path)
    worksheet = workbook[sheet_name]

    # 遍历第一行，查找含有 '歌词颜色' 的列
    column_letter = None
    for cell in worksheet[1]:  # 遍历第一行
        if cell.value == col_name:
            column_letter = cell.column_letter  # 获取列字母
            break

    # 获取该列第二行单元格
    cell = worksheet[f'{column_letter}{row_no}']  # 获取row_no行该列的单元格

    # 获取该单元格的颜色 (前景色)
    fill_color = cell.fill.fgColor.rgb
    rgb_color = fill_color[2:]  # 获取RGB部分 '112233'

    # 将颜色转换为 RGB 分量
    red = int(rgb_color[0: 2], 16)  # '11' -> 17
    green = int(rgb_color[2: 4], 16)  # '22' -> 34
    blue = int(rgb_color[4: 6], 16)  # '33' -> 51

    # 使用 python-pptx 的 RGBColor
    return blue << 16 | green << 8 | red


def save_ppt(new_ppt, filename):
    # 删除示例的幻灯片（3张），幻灯片id以1开始
    # 获取所有幻灯片
    slides = new_ppt.Slides
    for _ in list(range(2)):
        slides(1).Delete()

    new_ppt.SaveAs(filename)
    new_ppt.Close()


def get_last_layout(ppt):
    slides = ppt.Slides
    # 记录所有幻灯片使用到的布局
    used_layouts = set()

    for slide in slides:
        # 获取幻灯片使用的布局
        layout = slide.CustomLayout
        used_layouts.add(layout)  # 将布局添加到集合中，确保唯一

    # 遍历幻灯片母版中的所有布局，获取最后一个布局
    last_layout = {}
    for master in ppt.Designs:
        layouts = master.SlideMaster.CustomLayouts
        for layout in layouts:
            if layout in used_layouts:
                last_layout = layout

    return slides, last_layout


if __name__ == "__main__":
    if len(sys.argv) != 4:
        exit()

    date = sys.argv[1]
    file_path = sys.argv[2]

    # 获取当前程序的绝对路径
    current_path = os.path.abspath(__file__)
    # 读取Excel文件
    dfs = pd.read_excel(file_path, sheet_name=None)
    # 提取设置列
    selected_columns = dfs[SETTING_SHEET][['只生成歌曲封面？', '生成动态歌词？', '是否繁体歌词？', '页眉高度（厘米）', '最大字体（Pt）', '歌词行间距离（Pt）']]
    for index, row in selected_columns.iterrows():
        if index == 0:
            IS_COVER_ONLY = row['只生成歌曲封面？'] == '是'
            IS_DYNAMIC_LYRIC = row['生成动态歌词？'] == '是'
            PADDING_TOP = cm_to_points(row['页眉高度（厘米）']) if IS_DYNAMIC_LYRIC else 4
            IS_TRADITIONAL = row['是否繁体歌词？'] == '是'
            MAX_FONT_SIZE_PT = row['最大字体（Pt）']
            LINE_SPACING = row['歌词行间距离（Pt）']

    SHOW_LEN_2_PTS[0]['font'] = MAX_FONT_SIZE_PT
    SHOW_LEN_2_PTS[0]['line'] = MAX_FONT_SIZE_PT * 4 / 3

    # 启动 PowerPoint 应用
    app = CreateObject("PowerPoint.Application")
    app.Visible = True

    # 打开现有的 PowerPoint 演示文稿
    pwd = os.getcwd()
    in_ppt = f"{pwd}/{sys.argv[3]}"
    out_ppt = template_ppt = app.Presentations.Open(in_ppt)

    slides, last_layout = get_last_layout(out_ppt)

    path = f'{pwd}/{date}'
    if not os.path.exists(path):
        os.makedirs(path)

    dt_object = datetime.fromtimestamp(time())
    new_file = f'{path}/{dt_object.strftime("%Y%m%d-%H%M%S")}.pptx'
    start_tm = time()
    selected_columns = dfs[LIST_SHEET][['歌曲', '歌手', '歌手数量', '合唱歌词颜色', '歌手1歌词颜色', '歌手2歌词颜色', '歌手3歌词颜色', '歌手4歌词颜色', '要修改的歌词', '修改后歌词', '指定酷我音乐歌曲ID', '指定网易云歌曲ID']]
    for index, row in selected_columns.iterrows():
        # //-//
        # if index != 0:
        #     break

        sfx = ''
        if IS_DYNAMIC_LYRIC:
            out_ppt = generate_ppt(out_ppt, row, index)
        else:
            new_file = f'{path}/{str(row["歌曲"])}.pptx'
            out_ppt.SaveCopyAs(new_file)
            new_ppt = app.Presentations.Open(new_file)
            # 获取所有幻灯片
            new_ppt = generate_ppt(new_ppt, row, index)
            save_ppt(new_ppt, new_file)

    if IS_DYNAMIC_LYRIC:
        save_ppt(out_ppt, new_file)

    app.Quit()
    print(f'用时：{time() - start_tm}秒')
