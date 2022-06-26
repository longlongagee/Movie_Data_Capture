import os
import re
import sys
import config
import typing
import logging

G_spat = re.compile(
    "^\w+\.(cc|com|net|me|club|jp|tv|xyz|biz|wiki|info|tw|us|de)@|^22-sht\.me|"
    "^(fhd|hd|sd|1080p|720p|4K)(-|_)|"
    "(-|_)(fhd|hd|sd|1080p|720p|4K|x264|x265|uncensored|leak)",
    re.IGNORECASE)


def get_number(debug: bool, file_path: str) -> str:
    """
    从文件路径中提取番号 from number_parser import get_number
    >>> get_number(False, "/Users/Guest/AV_Data_Capture/snis-829.mp4")
    'snis-829'
    >>> get_number(False, "/Users/Guest/AV_Data_Capture/snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, "/Users/Guest/AV_Data_Capture/[脸肿字幕组][PoRO]牝教師4～穢された教壇～ 「生意気ドジっ娘女教師・美結～高飛車ハメ堕ち2濁金」[720p][x264_aac].mp4")
    '牝教師4～穢された教壇～ 「生意気ドジっ娘女教師・美結～高飛車ハメ堕ち2濁金」'
    >>> get_number(False, "C:¥Users¥Guest¥snis-829.mp4")
    'snis-829'
    >>> get_number(False, "C:¥Users¥Guest¥snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, "./snis-829.mp4")
    'snis-829'
    >>> get_number(False, "./snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, ".¥snis-829.mp4")
    'snis-829'
    >>> get_number(False, ".¥snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, "snis-829.mp4")
    'snis-829'
    >>> get_number(False, "snis-829-C.mp4")
    'snis-829'
    """
    filepath = os.path.basename(file_path)
    # debug True 和 False 两块代码块合并，原因是此模块及函数只涉及字符串计算，没有IO操作，debug on时输出导致异常信息即可

    def filter_len(file_number):
        if len(file_number) < 5:
            logging.info(f" 太短了:{file_number}")
            return None

        for _ in ['000K_', '1080P', '480P', '720P','360P']:
            if _ in file_number:
                return None

        return file_number

    try:
        file_number = get_number_by_dict(filepath)

        if file_number:
            return filter_len(file_number)
        elif '字幕组' in filepath or 'SUB' in filepath.upper() or re.match(r'[\u30a0-\u30ff]+', filepath):
            filepath = G_spat.sub("", filepath)
            filepath = re.sub("\[.*?\]","",filepath)
            filepath = filepath.replace(".chs", "").replace(".cht", "")
            file_number = str(re.findall(r'(.+?)\.', filepath)).strip(" [']")
            return filter_len(file_number)
        elif '-' in filepath or '_' in filepath or ' ' in filepath:  # 普通提取番号 主要处理包含减号-和_的番号
            filepath = G_spat.sub("", filepath)
            filename = str(re.sub("\[\d{4}-\d{1,2}-\d{1,2}\] - ", "", filepath))  # 去除文件名中时间
            lower_check = filename.lower()
            if 'fc2' in lower_check:
                filename = lower_check.replace('ppv', '').replace(' ', '-').replace('--', '-').replace('_', '-').upper()
            filename = re.sub("[-_]cd\d{1,2}", "", filename, flags=re.IGNORECASE)
            if not re.search("-|_", filename): # 去掉-CD1之后再无-的情况，例如n1012-CD1.wmv
                return filter_len(str(re.search(r'\w+', filename[:filename.find('.')], re.A).group()))

            # 不连续多个 -
            result = re.findall(r'\w+[-_]\w+', filename, re.A)
            if len(result) > 1:
                for _ in result:
                    if re.search(r'\d{2,}', _):
                        file_number = _
                        break
            else:
                file_number = result[0]

            # 连续多个 - ，取数字 + 分类
            if not re.search(r'\d{2,}', file_number):
                if re.search(r"\w+[-_]\w+[-_]\w+", filename):
                    filename = filename.replace('_', '-').replace('--', '-')
                    if filename.count('-') > 1:
                        filename_list = filename.split('-')
                        for _ in filename.split('-'):
                            if re.search(r'\d{2,}', _) and filename_list.index(_) > 1:
                                file_number = filename_list[filename_list.index(_)-1] + '-' + _
                                break

                file_number = re.findall(r'\w+[-_]\w+', file_number)[0]

            file_number = re.sub("(-|_)c$", "", file_number, flags=re.IGNORECASE)
            if re.search("\d+ch$", file_number, flags=re.I):
                file_number = file_number[:-2]

            # 另一种FC2
            # if 'FC2' in file_number:
            #     file_number = file_number.replace('FC2-', 'FC2-PPV-')

            return filter_len(file_number.upper())

        else:  # 提取不含减号-的番号，FANZA CID
            # 欧美番号匹配规则
            oumei = re.search(r'[a-zA-Z]+\.\d{2}\.\d{2}\.\d{2}', filepath)
            if oumei:
                return filter_len(oumei.group())
            try:
                return str(
                    re.findall(r'(.+?)\.',
                               str(re.search('([^<>/\\\\|:""\\*\\?]+)\\.\\w+$', filepath).group()))).strip(
                    "['']").replace('_', '-')
            except:
                return filter_len(str(re.search(r'(.+?)\.', filepath)[0]))
    except Exception as e:
        if debug:
            print(f'[-]Number Parser exception: {e} [{file_path}]')
        return None


# modou提取number
def md(filename):
    m = re.search(r'(md[a-z]{0,2}-?)(\d{2,})(-ep\d*)*', filename, re.I)
    return f'{m.group(1).replace("-","").upper()}{m.group(2).zfill(4)}{m.group(3) or ""}'


def mmz(filename):
    m = re.search(r'(mmz-?)(\d{2,})(-ep\d*)*', filename, re.I)
    return f'{m.group(1).replace("-","").upper()}{m.group(2).zfill(3)}{m.group(3) or ""}'


def msd(filename):
    m = re.search(r'(msd-?)(\d{2,})(-ep\d*)*', filename, re.I)
    return f'{m.group(1).replace("-","").upper()}{m.group(2).zfill(3)}{m.group(3) or ""}'


def mky(filename):
    m = re.search(r'(mky-[a-z]{2,2}-?)(\d{2,})(-ep\d*)*', filename, re.I)
    return f'{m.group(1).replace("-","").upper()}{m.group(2).zfill(3)}{m.group(3) or ""}'


def yk(filename):
    m = re.search(r'(yk-?)(\d{2,})(-ep\d*)*', filename, re.I)
    return f'{m.group(1).replace("-","").upper()}{m.group(2).zfill(3)}{m.group(3) or ""}'


def pm(filename):
    m = re.search(r'(pm[a-z]?-?)(\d{2,})(-ep\d*)*', filename, re.I)
    return f'{m.group(1).replace("-","").upper()}{m.group(2).zfill(3)}{m.group(3) or ""}'   


def av9898(filename):
    # 括号处理
    # if '(' in filename and ')' in filename:
    #     filename = filename.replace("(", '-').replace(")", "-").replace('--', '-').strip('-')
    file_number = str(re.search(r'\(.*\d+[-_]\d+\)', filename, re.A).group())
    return file_number


# 按javdb数据源的命名规范提取number
G_TAKE_NUM_RULES = {
    'tokyo.*hot': lambda x: str(re.search(r'(cz|gedo|k|n|red-|se)\d{2,4}', x, re.I).group()),
    'carib': lambda x: str(re.search(r'\d{6}(-|_)\d{3}', x, re.I).group()).replace('_', '-'),
    '1pon|mura|paco': lambda x: str(re.search(r'\d{6}(-|_)\d{3}', x, re.I).group()).replace('-', '_'),
    '10mu': lambda x: str(re.search(r'\d{6}(-|_)\d{2}', x, re.I).group()).replace('-', '_'),
    'x-art': lambda x: str(re.search(r'x-art\.\d{2}\.\d{2}\.\d{2}', x, re.I).group()),
    'xxx-av': lambda x: ''.join(['xxx-av-', re.findall(r'xxx-av[^\d]*(\d{3,5})[^\d]*', x, re.I)[0]]),
    'heydouga': lambda x: 'heydouga-' + '-'.join(re.findall(r'(\d{4})[\-_](\d{3,4})[^\d]*', x, re.I)[0]),
    'heyzo': lambda x: 'HEYZO-' + re.findall(r'heyzo[^\d]*(\d{4})', x, re.I)[0],
    r'\bmd[a-z]{0,2}-\d{2,}': md,
    r'\bmmz-\d{2,}':mmz,
    r'\bmsd-\d{2,}':msd,
    r'\bmky-[a-z]{2,2}-\d{2,}':mky,
    r'\byk-\d{2,3}': yk,
    r'\bpm[a-z]?-?\d{2,}':pm,
    '糖心Vlog': lambda x: str(re.search(r'(.*?)\.\w+', x).groups()[0]).rsplit('_', 1)[0].strip(' #'),
    'AV9898': av9898,
    # '10musume': lambda x: '10musume' + str(re.search(r'\d{}6', x).groups()[0]),
}


def get_number_by_dict(filename: str) -> typing.Optional[str]:
    try:
        for k, v in G_TAKE_NUM_RULES.items():
            if re.search(k, filename, re.I):
                return v(filename)
    except:
        pass
    return None


class Cache_uncensored_conf:
    prefix = None

    def is_empty(self):
        return bool(self.prefix is None)

    def set(self, v: list):
        if not v or not len(v) or not len(v[0]):
            raise ValueError('input prefix list empty or None')
        s = v[0]
        if len(v) > 1:
            for i in v[1:]:
                s += f"|{i}.+"
        self.prefix = re.compile(s, re.I)

    def check(self, number):
        if self.prefix is None:
            raise ValueError('No init re compile')
        return self.prefix.match(number)


G_cache_uncensored_conf = Cache_uncensored_conf()


# ========================================================================是否为无码
def is_uncensored(number) -> bool:
    if re.match(
            r'[\d-]{4,}|\d{6}_\d{2,3}|(cz|gedo|k|n|red-|se)\d{2,4}|heyzo.+|xxx-av-.+|heydouga-.+|x-art\.\d{2}\.\d{2}\.\d{2}',
            number,
            re.I
    ):
        return True
    if G_cache_uncensored_conf.is_empty():
        G_cache_uncensored_conf.set(config.getInstance().get_uncensored().split(','))
    return bool(G_cache_uncensored_conf.check(number))


if __name__ == "__main__":
    #     import doctest
    #     doctest.testmod(raise_on_error=True)
    test_use_cases = (
        "MEYD-594-C.mp4",
        "SSIS-001_C.mp4",
        "SSIS100-C.mp4",
        "SSIS101_C.mp4",
        "ssni984.mp4",
        "ssni666.mp4",
        "SDDE-625_uncensored_C.mp4",
        "SDDE-625_uncensored_leak_C.mp4",
        "SDDE-625_uncensored_leak_C_cd1.mp4",
        "Tokyo Hot n9001 FHD.mp4",  # 无-号，以前无法正确提取
        "TokyoHot-n1287-HD SP2006 .mp4",
        "caribean-020317_001.nfo",  # -号误命名为_号的
        "257138_3xplanet_1Pondo_080521_001.mp4",
        "ADV-R0624-CD3.wmv",  # 多碟影片
        "XXX-AV   22061-CD5.iso",  # 支持片商格式 xxx-av-22061 命名规则来自javdb数据源
        "xxx-av 20589.mp4",
        "Muramura-102114_145-HD.wmv",  # 支持片商格式 102114_145  命名规则来自javdb数据源
        "heydouga-4102-023-CD2.iso",  # 支持片商格式 heydouga-4102-023 命名规则来自javdb数据源
        "HeyDOuGa4236-1048 Ai Qiu - .mp4",  # heydouga-4236-1048 命名规则来自javdb数据源
        "pacopacomama-093021_539-FHD.mkv",  # 支持片商格式 093021_539 命名规则来自javdb数据源
        "sbw99.cc@heyzo_hd_2636_full.mp4",
        "hhd800.com@STARS-566-HD.mp4",
        "jav20s8.com@GIGL-677_4K.mp4",
        "sbw99.cc@iesp-653-4K.mp4",
        "4K-ABP-358_C.mkv",
        "n1012-CD1.wmv",
        "[]n1012-CD2.wmv",
        "rctd-460ch.mp4",  # 除支持-C硬字幕外，新支持ch硬字幕
        "rctd-461CH-CD2.mp4",  # ch后可加CDn
        "rctd-461-Cd3-C.mp4",  # CDn后可加-C
        "rctd-461-C-cD4.mp4",  # cD1 Cd1 cd1 CD1 最终生成.nfo时统一为大写CD1
        "MD-123.ts",
        "MDSR-0001-ep2.ts",
        "MKY-NS-001.mp4"
    )


    # def evprint(evstr):
    #     code = compile(evstr, "<string>", "eval")
    #     print("{1:>20} # '{0}'".format(evstr[18:-2], eval(code)))
    #
    #
    # for t in test_use_cases:
    #     evprint(f'get_number(True, "{t}")')
    #
    # if len(sys.argv) <= 1 or not re.search('^[A-Z]:?', sys.argv[1], re.IGNORECASE):
    #     sys.exit(0)
    #
    # # 使用Everything的ES命令行工具搜集全盘视频文件名作为用例测试number数据，参数为盘符 A .. Z 或带盘符路径
    # # https://www.voidtools.com/support/everything/command_line_interface/
    # # ES命令行工具需要Everything文件搜索引擎处于运行状态，es.exe单个执行文件需放入PATH路径中。
    # # Everything是免费软件
    # # 示例：
    # # python.exe .\number_parser.py ALL                 # 从所有磁盘搜索视频
    # # python.exe .\number_parser.py D                   # 从D盘搜索
    # # python.exe .\number_parser.py D:                  # 同上
    # # python.exe .\number_parser.py D:\download\JAVs    # 搜索D盘的\download\JAVs目录，路径必须带盘符
    # # ==================
    # # Linux/WSL1|2 使用mlocate(Ubuntu/Debian)或plocate(Debian sid)搜集全盘视频文件名作为测试用例number数据
    # # 需安装'sudo apt install mlocate或plocate'并首次运行sudo updatedb建立全盘索引
    # # MAC OS X 使用findutils的glocate，需安装'sudo brew install findutils'并首次运行sudo gupdatedb建立全盘索引
    # # 示例：
    # # python3 ./number_parser.py ALL
    # import subprocess
    #
    # ES_search_path = "ALL disks"
    # if sys.argv[1] == "ALL":
    #     if sys.platform == "win32":
    #         # ES_prog_path = 'C:/greensoft/es/es.exe'
    #         ES_prog_path = 'es.exe'  # es.exe需要放在PATH环境变量的路径之内
    #         ES_cmdline = f'{ES_prog_path} -name size:gigantic ext:mp4;avi;rmvb;wmv;mov;mkv;flv;ts;webm;iso;mpg;m4v'
    #         out_bytes = subprocess.check_output(ES_cmdline.split(' '))
    #         out_text = out_bytes.decode('gb18030')  # 中文版windows 10 x64默认输出GB18030，此编码为UNICODE方言与UTF-8系全射关系无转码损失
    #         out_list = out_text.splitlines()
    #     elif sys.platform in ("linux", "darwin"):
    #         ES_prog_path = 'locate' if sys.platform == 'linux' else 'glocate'
    #         ES_cmdline = r"{} -b -i --regex '\.mp4$|\.avi$|\.rmvb$|\.wmv$|\.mov$|\.mkv$|\.webm$|\.iso$|\.mpg$|\.m4v$'".format(
    #             ES_prog_path)
    #         out_bytes = subprocess.check_output(ES_cmdline.split(' '))
    #         out_text = out_bytes.decode('utf-8')
    #         out_list = [os.path.basename(line) for line in out_text.splitlines()]
    #     else:
    #         print('[-]Unsupported platform! Please run on OS Windows/Linux/MacOSX. Exit.')
    #         sys.exit(1)
    # else:  # Windows single disk
    #     if sys.platform != "win32":
    #         print('[!]Usage: python3 ./number_parser.py ALL')
    #         sys.exit(0)
    #     # ES_prog_path = 'C:/greensoft/es/es.exe'
    #     ES_prog_path = 'es.exe'  # es.exe需要放在PATH环境变量的路径之内
    #     if os.path.isdir(sys.argv[1]):
    #         ES_search_path = sys.argv[1]
    #     else:
    #         ES_search_path = sys.argv[1][0] + ':/'
    #         if not os.path.isdir(ES_search_path):
    #             ES_search_path = 'C:/'
    #         ES_search_path = os.path.normcase(ES_search_path)
    #     ES_cmdline = f'{ES_prog_path} -path {ES_search_path} -name size:gigantic ext:mp4;avi;rmvb;wmv;mov;mkv;webm;iso;mpg;m4v'
    #     out_bytes = subprocess.check_output(ES_cmdline.split(' '))
    #     out_text = out_bytes.decode('gb18030')  # 中文版windows 10 x64默认输出GB18030，此编码为UNICODE方言与UTF-8系全射关系无转码损失
    #     out_list = out_text.splitlines()
    # print(f'\n[!]{ES_prog_path} is searching {ES_search_path} for movies as number parser test cases...')
    # print(f'[+]Find {len(out_list)} Movies.')
    # for filename in out_list:
    #     try:
    #         n = get_number(True, filename)
    #         if n:
    #             print('  [{0}] {2}# {1}'.format(n, filename, '#无码' if is_uncensored(n) else ''))
    #         else:
    #             print(f'[-]Number return None. # {filename}')
    #     except Exception as e:
    #         print(f'[-]Number Parser exception: {e} [{filename}]')
    #
    # sys.exit(0)

    cases = r"""
    \\NAS\smb\videos\JAV_output\大島さくら32歳製薬会社役員の妻\300MIUM-680\300MIUM-680-C.mp4
    \\NAS\smb\videos\JAV_output\マリア・ナ・カイキョー21歳現役JD∕生徒を喰っちゃうヘンタイ家庭教師\390JNT-023\390JNT-023.mp4
    \\NAS\smb\videos\AVI三次元\#糖心Vlog_圣诞2021_圣诞夜寂寞酒店之旅_更多精彩内容TG频道@zuichunlou.mp4
    \\NAS\smb\videos\JAV_output\魔人petit\GETCHU-1163796\GETCHU-1163796.mp4
    \\NAS\smb\videos\JAV_output\メディアファクトリー\GETCHU-996117\GETCHU-996117.mp4
    \\NAS\smb\videos\JAV_output\桃狐の変態調教課題\RJ374870\RJ374870.mp4
    \\NAS\smb\videos\JAV_output\桃狐の変態調教課題\RJ374870\RJ374870.mkv
    \\NAS\smb\videos\JAV_output\エイト・ワールド\RJ174616\RJ174616.mp4
    \\NAS\smb\videos\JAV_output\アニプレックス\GETCHU-175701\GETCHU-175701.mp4
    \\NAS\smb\videos\JAV_output\アニプレックス\GETCHU-988997\GETCHU-988997.mp4
    \\NAS\smb\videos\JAV_output\ナイトホーク\RJ383477\RJ383477.mp4
    \\NAS\smb\videos\JAV_output\ティンクルベル\RJ017698\RJ017698.mp4
    \\NAS\smb\videos\JAV_output\りりー☆くり～む\RJ228113\RJ228113.mp4
    \\NAS\smb\videos\JAV_output\studioGGB\RJ146890\RJ146890.mp4
    \\NAS\smb\videos\JAV_output\ハピネット・ピクチャーズ\GETCHU-249520\GETCHU-249520.mp4
    \\NAS\smb\videos\JAV_output\家庭菜園\RJ390519\RJ390519.wmv
    \\NAS\smb\videos\JAV_output\オーガスト\VJ012288\VJ012288.mp4
    \\NAS\smb\videos\JAV_output\ガチピンのSS部屋\RJ393849\RJ393849.mp4
    \\NAS\smb\videos\JAV_output\Lantis\GETCHU-1135078\GETCHU-1135078.rmvb
    \\NAS\smb\videos\JAV_output\Lantis\GETCHU-1135078\GETCHU-1135078.mp4
    \\NAS\smb\videos\JAV_output\Lantis\GETCHU-1135078\GETCHU-1135078.mkv
    \\NAS\smb\videos\JAV_output\（このブランドの作品一覧）\GETCHU-1139626\GETCHU-1139626.rmvb
    \\NAS\smb\videos\JAV_output\（このブランドの作品一覧）\GETCHU-788964\GETCHU-788964.mkv
    \\NAS\smb\videos\JAV_output\FreakilyCharming\RJ141907\RJ141907.mkv
    \\NAS\smb\videos\JAV_output\むこね屋\RJ287317\RJ287317.mp4
    \\NAS\smb\videos\JAV_output\幻伍楼\RJ393977\RJ393977.mp4
    \\NAS\smb\videos\JAV_output\CATWU\RJ392856\RJ392856.mp4
    \\NAS\smb\videos\JAV_output\メリー・ジェーン\GETCHU-774256\GETCHU-774256-C.mp4
    \\NAS\smb\videos\JAV_output\メリー・ジェーン\VJ008165\VJ008165.mkv
    \\NAS\smb\videos\JAV_output\メリー・ジェーン\VJ008165\VJ008165.mp4
    \\NAS\smb\videos\JAV_output\PoROre꞉\VJ008039\VJ008039.mkv
    \\NAS\smb\videos\JAV_output\PoROre꞉\VJ008631\VJ008631.mp4
    \\NAS\smb\videos\JAV_output\PoRO\GETCHU-930294\GETCHU-930294.mkv
    \\NAS\smb\videos\JAV_output\ピンクパイナップル\GETCHU-1023466\GETCHU-1023466.mkv
    \\NAS\smb\videos\JAV_output\ピンクパイナップル\GETCHU-847658\GETCHU-847658-C.mp4
    \\NAS\smb\videos\JAV_output\KADOKAWA\GETCHU-342025\GETCHU-342025.mp4
    \\NAS\smb\videos\JAV_output\NBCユニバーサル・エンターテイメントジャパン\GETCHU-773669\GETCHU-773669.mp4
    \\NAS\smb\videos\JAV_output\エイベックス\GETCHU-731144\GETCHU-731144.mp4
    \\NAS\smb\videos\JAV_output\ブシロードミュージック\GETCHU-1170317\GETCHU-1170317.mp4
    \\NAS\smb\videos\AVI三次元\(6)sadfasdcsadc.mp4
    \\NAS\smb\videos\AVI三次元\(AV9898)(4030-1739)グラマラス 酒井ももか.mp4
    \\NAS\smb\videos\AVI三次元\(E-BODY)(EBOD-578)お屋敷のいたるところで献身的おっぱいサービス！Kcup超々セクシーランジェリーメイド 深田ナナ.mp4
    \\NAS\smb\vAAXV.a234=XYZ-FC2-1945430.MP4
    """
    import os

    def _find_mp4(fl):
        fl = os.listdir(fl)
        new_list = []
        regex = re.compile(r'.*?(\.mp4|\.avi|\.mkv)')
        for file_name in fl:
            if regex.search(file_name):
                new_list.append(file_name)
        return new_list


    cases = _find_mp4(r'\\NAS\smb\videos\待定')
    for case in cases:
        case = case.strip()
        if case:
            print(case, '==>', get_number(False, case))

