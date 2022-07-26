from datetime import datetime, timedelta
import threading


def s32(integer: int) -> int:
    return ((integer & 0xffffffff) ^ 0x80000000) - 0x80000000


def datetime_to_seed(datetime: int) -> int:
    seed = s32(datetime + 1)
    seed = s32(s32(seed * 1108104919) + 11786)
    seed = s32(s32(seed * 1566083941) + 15413)
    seed = s32(s32(seed >> 16) + s32(seed << 16))
    if seed >= 0:
        return seed
    else:
        return 0x100000000 + seed


class Clock:
    def __init__(self, alarms: list[datetime]) -> None:
        self.alarms = alarms
        self._stopped = threading.Event()
        self._thread = threading.Thread(
            target=self.print_time_now, daemon=True)

    def start(self) -> None:
        if not self._stopped.is_set():
            self._thread.start()

    def stop(self) -> None:
        self._stopped.set()

    def print_time_now(self) -> None:
        self._stopped.wait(0.5)
        print()
        string = ''
        while not self._stopped.wait(0.01):
            try:
                current_alarm = self.alarms.pop(0)
            except IndexError:
                break
            t = current_alarm - datetime.now()
            time_until_alarm = 0
            while time_until_alarm >= 0 and not self._stopped.wait(0.01):
                time_now = datetime.now()
                t = current_alarm - time_now
                time_until_alarm = ((t.days * 3600 * 24)
                                    + t.seconds
                                    + t.microseconds / 1000000)
                time_now = time_now.strftime('%d/%m/%Y %H:%M:%S')
                string = (f'Time now: {time_now} | '
                          f'Time until next seed: {time_until_alarm:7.3f}')
                print(string, end='\r')
            print('\a', end='')
        print(' ' * len(string), end='\r')
        while not self._stopped.wait(0.1):
            time_now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            print(f'Time now: {time_now}', end='\r')


def countdown(seconds: int = 5) -> None:
    input(f'Once you press enter a countdown of {seconds} seconds '
          'will begin. Press new game once it reaches 0.')
    time_now = datetime.now().replace(microsecond=0)
    countdown_time = time_now + timedelta(seconds=seconds)
    time_until_new_game = 0
    while time_until_new_game >= 0:
        time_now = datetime.now()
        t = countdown_time - time_now
        time_until_new_game = ((t.days * 3600 * 24)
                               + t.seconds
                               + t.microseconds / 1000000)
        time_now = time_now.strftime('%d/%m/%Y %H:%M:%S')
        string = (f'Time now: {time_now} | '
                  f'Time until new game: {time_until_new_game:7.3f}')
        print(string, end='\r')
    print('\a', end='')
    print(' ' * len(string), end='\r')


def get_mystery_byte() -> int:
    dt = datetime.now()
    print(f'Time when pressing new game: {dt.strftime("%d/%m/%Y %H:%M:%S")}')
    dt = dt + ONE_SECOND
    xored_datetime = (dt.day
                      ^ dt.month
                      ^ int(hex(dt.year)[-2:], 16)
                      ^ dt.hour
                      ^ dt.minute
                      ^ dt.second
                      )
    while True:
        input_string = input('Damage values (Auron1 Tidus Auron2):')
        # replace different symbols with spaces
        for symbol in (',', '-', '/', '\\', '.'):
            input_string = input_string.replace(symbol, ' ')
        input_dvs_strings = input_string.split()
        try:
            input_dvs = tuple([int(i) for i in input_dvs_strings])
        except ValueError as error:
            error = str(error).split(':', 1)[1]
            print(f'{error} is not a valid damage value.')
            continue
        if len(input_dvs) != 3:
            print('Need 3 damage values.')
            continue
        for seed, dvs in SEEDS_TO_DVS.items():
            if dvs == input_dvs:
                break
        else:
            print('Seed not found.')
            continue
        if seed not in SEEDS_TO_DVS:
            print('Seed number invalid!')
            continue
        for mystery_byte in range(256):
            if seed == datetime_to_seed(xored_datetime ^ mystery_byte):
                print(f'\nMystery byte: {mystery_byte}\n')
                break
        else:
            continue
        break
    return mystery_byte


def main(use_countdown: bool = False):
    possible_seeds = [s for s in SEEDS_TO_DVS]
    while True:
        try:
            target_seed = int(input('Type the seed (ID or Number) you want: '))
        except ValueError:
            print('Seed must be an integer.')
            continue
        if 0 <= target_seed <= 255:
            target_seed = possible_seeds[target_seed]
        elif target_seed not in SEEDS_TO_DVS:
            print(f'Seed {target_seed} is not available on FFX PC version.')
            continue
        break

    print(f'Picked seed {possible_seeds.index(target_seed)} ({target_seed}).')

    while True:
        while True:
            mystery_byte = input('If you have it already, type your mystery '
                                 'byte, otherwise just press enter: ')
            if mystery_byte == '':
                if use_countdown:
                    countdown()
                else:
                    clock = Clock([])
                    clock.start()
                    input('Press enter and new game at the same time.')
                    clock.stop()
                mystery_byte = get_mystery_byte()
                break
            try:
                mystery_byte = int(mystery_byte)
            except ValueError:
                print('Mystery byte must be an integer between 0 and 255.')
                continue
            if not (0 <= mystery_byte <= 255):
                print('Mystery byte must be an integer between 0 and 255.')
                continue
            break

        while True:
            dt = datetime.now().replace(microsecond=0)
            times: list[datetime] = []
            for _ in range(600):
                dt = dt + ONE_SECOND
                # only the last 2 digits of the year are used
                # and they are treated as an hex number
                xored_datetime = (dt.day
                                  ^ dt.month
                                  ^ int(hex(dt.year)[-2:], 16)
                                  ^ dt.hour
                                  ^ dt.minute
                                  ^ dt.second
                                  ^ mystery_byte)
                if target_seed == datetime_to_seed(xored_datetime):
                    dt_real = dt - ONE_SECOND
                    times.append(dt_real)
            if times:
                print('Press new game at one of these seconds '
                      f'to get seed {target_seed}:')
                for time in times:
                    print(f'    {time.strftime("%d/%m/%Y %H:%M:%S")}')
                clock = Clock(times)
                clock.start()
                input('Press enter to restart.')
                clock.stop()
                return
            else:
                print(f'Impossible to manip seed {target_seed} '
                      f'with mystery byte {mystery_byte}.\n'
                      'Restart the game to reroll the mystery byte.')
                break


ONE_SECOND = timedelta(seconds=1)
SEEDS_TO_DVS = {
    3556394350: (269, 133, 288),
    3553426523: (279, 132, 294),
    3550458696: (260, 134, 274),
    3547556405: (276, 136, 556),
    3544588578: (274, 131, 263),
    3541620751: (271, 134, 285),
    3538652924: (269, 250, 284),
    3535750633: (272, 133, 275),
    3532782806: (582, 139, 274),
    3529814979: (286, 132, 260),
    3526912688: (538, 135, 263),
    3523944861: (267, 278, 288),
    3520977034: (526, 129, 260),
    3518009207: (570, 130, 278),
    3515106916: (271, 262, 271),
    3512139089: (270, 129, 279),
    3509171262: (268, 139, 534),
    3506268971: (574, 127, 281),
    3503301144: (286, 134, 267),
    3500333317: (264, 128, 262),
    3497365490: (568, 125, 266),
    3494463199: (540, 136, 578),
    3491495372: (283, 138, 288),
    3488527545: (274, 260, 278),
    3485625254: (281, 139, 546),
    3482657427: (274, 135, 562),
    3479689600: (279, 137, 269),
    3476721773: (263, 125, 564),
    3473819482: (560, 136, 572),
    3470851655: (270, 137, 276),
    3467883828: (267, 125, 552),
    3464981537: (291, 274, 279),
    3462013710: (275, 258, 286),
    3459045883: (572, 131, 273),
    3456078056: (274, 139, 272),
    3453175765: (564, 270, 289),
    3450207938: (284, 134, 284),
    3447240111: (526, 128, 267),
    3444337820: (275, 264, 283),
    3441369993: (285, 136, 283),
    3438402166: (272, 276, 267),
    3435434339: (538, 128, 260),
    3432532048: (274, 134, 270),
    3429564221: (534, 135, 534),
    3426596394: (279, 135, 270),
    3423694103: (538, 139, 266),
    3420726276: (281, 136, 526),
    3417758449: (560, 268, 276),
    3414790622: (283, 262, 283),
    3411888331: (274, 262, 275),
    3408920504: (260, 138, 287),
    3405952677: (294, 128, 282),
    3403050386: (263, 128, 570),
    3400082559: (578, 129, 281),
    3397114732: (282, 138, 562),
    3394146905: (262, 132, 278),
    3391244614: (271, 136, 264),
    3388276787: (270, 132, 536),
    3385308960: (546, 129, 274),
    3382406669: (284, 129, 285),
    3379438842: (526, 132, 289),
    3376471015: (264, 258, 291),
    3373503188: (272, 138, 273),
    3370600897: (266, 126, 269),
    3367633070: (293, 126, 287),
    3364665243: (267, 254, 271),
    3361762952: (284, 141, 280),
    3358795125: (261, 126, 281),
    3355827298: (282, 139, 283),
    3352859471: (284, 130, 272),
    3349957180: (291, 135, 292),
    3346989353: (260, 141, 281),
    3344021526: (280, 132, 280),
    3341119235: (284, 268, 291),
    3338151408: (283, 136, 284),
    3335183581: (283, 132, 291),
    3332215754: (261, 138, 264),
    3329313463: (280, 274, 291),
    3326345636: (538, 140, 270),
    3323377809: (280, 141, 266),
    3320475518: (278, 134, 289),
    3317507691: (283, 278, 275),
    3314539864: (281, 254, 538),
    3311572037: (275, 141, 276),
    3308669746: (287, 140, 270),
    3305701919: (281, 131, 274),
    3302734092: (280, 254, 287),
    3299831801: (263, 133, 269),
    3296863974: (291, 262, 281),
    3293896147: (546, 270, 268),
    3290928320: (276, 268, 289),
    3288026029: (273, 138, 275),
    3285058202: (268, 132, 289),
    3282090375: (271, 128, 284),
    3279188084: (278, 135, 582),
    3276220257: (582, 137, 560),
    3273252430: (293, 130, 292),
    3270284603: (270, 128, 528),
    3267382312: (263, 141, 261),
    3264414485: (266, 138, 564),
    3261446658: (276, 141, 274),
    3258544367: (272, 139, 534),
    3255576540: (284, 282, 267),
    3252608713: (273, 138, 283),
    3249640886: (267, 141, 280),
    3246738595: (281, 136, 546),
    3243770768: (274, 129, 281),
    3240802941: (288, 135, 538),
    3237900650: (264, 131, 287),
    3234932823: (586, 127, 273),
    3231964996: (276, 262, 278),
    3228997169: (267, 140, 285),
    3226094878: (273, 126, 273),
    3223127051: (540, 126, 287),
    3220159224: (522, 132, 263),
    3217256933: (284, 125, 288),
    3214289106: (283, 137, 260),
    3211321279: (261, 135, 294),
    3208353452: (562, 272, 528),
    3205451161: (534, 280, 279),
    3202483334: (586, 139, 293),
    3199515507: (293, 130, 532),
    3196613216: (268, 134, 270),
    3193645389: (271, 132, 288),
    3190677562: (267, 134, 291),
    3187709735: (280, 252, 293),
    3184807444: (278, 128, 282),
    3181839617: (291, 128, 274),
    3178871790: (294, 134, 269),
    3175969499: (289, 132, 278),
    3173001672: (276, 260, 260),
    3170033845: (271, 132, 276),
    3167066018: (287, 126, 271),
    3164163727: (286, 254, 280),
    3161195900: (270, 128, 283),
    3158228073: (276, 126, 280),
    3155325782: (263, 256, 286),
    3152357955: (528, 278, 578),
    3149390128: (283, 272, 267),
    3146422301: (266, 137, 273),
    3143520010: (281, 131, 285),
    3140552183: (267, 136, 282),
    3137584356: (289, 129, 293),
    3134682065: (556, 127, 566),
    3131714238: (262, 132, 279),
    3128746411: (268, 136, 274),
    3125778584: (268, 132, 261),
    3122876293: (271, 127, 544),
    3119908466: (273, 138, 269),
    3116940639: (528, 131, 281),
    3114038348: (293, 258, 263),
    3111070521: (289, 127, 272),
    3108102694: (272, 134, 293),
    3105134867: (271, 133, 267),
    3102232576: (584, 130, 284),
    3099264749: (273, 270, 284),
    3096296922: (526, 262, 263),
    3093394631: (273, 131, 275),
    3090426804: (267, 138, 289),
    3087458977: (289, 131, 536),
    3084491150: (282, 136, 273),
    3081588859: (282, 129, 281),
    3078621032: (279, 132, 280),
    3075653205: (266, 130, 275),
    3072750914: (268, 141, 536),
    3069783087: (520, 136, 582),
    3066815260: (279, 141, 562),
    3063847433: (568, 268, 264),
    3060945142: (293, 126, 263),
    3057977315: (270, 129, 582),
    3055009488: (263, 140, 584),
    3052107197: (272, 141, 280),
    3049139370: (268, 139, 540),
    3046171543: (274, 266, 264),
    3043203716: (263, 252, 278),
    3040301425: (568, 131, 273),
    3037333598: (279, 268, 279),
    3034365771: (279, 126, 282),
    3031463480: (281, 132, 576),
    3028495653: (286, 131, 284),
    3025527826: (283, 274, 285),
    3022559999: (267, 258, 522),
    3019657708: (276, 139, 274),
    3016689881: (281, 127, 280),
    3013722054: (285, 264, 281),
    3010819763: (260, 125, 291),
    3007851936: (286, 132, 276),
    3004884109: (275, 125, 267),
    3001916282: (260, 140, 542),
    2999013991: (283, 136, 274),
    2996046164: (264, 250, 273),
    2993078337: (278, 137, 292),
    2990176046: (268, 131, 570),
    2987208219: (558, 141, 294),
    2984240392: (286, 268, 292),
    2981272565: (281, 132, 292),
    2978370274: (276, 135, 294),
    2975402447: (276, 270, 281),
    2972434620: (568, 129, 522),
    2969532329: (261, 139, 582),
    2966564502: (283, 137, 566),
    2963596675: (261, 141, 275),
    2960628848: (268, 133, 271),
    2957726557: (275, 137, 270),
    2954758730: (272, 258, 261),
    2951790903: (268, 126, 568),
    2948888612: (292, 138, 291),
    2945920785: (287, 129, 570),
    2942952958: (285, 274, 285),
    2939985131: (267, 141, 272),
    2937082840: (269, 130, 282),
    2934115013: (289, 127, 287),
    2931147186: (269, 141, 292),
    2928244895: (292, 131, 266),
    2925277068: (284, 136, 292),
    2922309241: (274, 135, 522),
    2919341414: (269, 134, 282),
    2916439123: (285, 128, 266),
    2913471296: (288, 126, 274),
    2910503469: (528, 131, 283),
    2907601178: (264, 138, 293),
    2904633351: (292, 254, 280),
    2901665524: (285, 125, 283),
    2898697697: (261, 133, 286),
    2895795406: (294, 139, 274),
    2892827579: (263, 140, 292),
    2889859752: (294, 130, 584),
    2886957461: (540, 132, 269),
    2883989634: (264, 125, 266),
    2881021807: (536, 130, 272),
    2878053980: (574, 125, 276),
    2875151689: (294, 135, 291),
    2872183862: (267, 132, 288),
    2869216035: (281, 134, 289),
    2866313744: (281, 262, 269),
    2863345917: (269, 282, 586),
    2860378090: (586, 134, 556),
    2857410263: (263, 136, 276),
    2854507972: (280, 127, 546),
    2851540145: (528, 137, 268),
    2848572318: (284, 268, 293),
    2845670027: (287, 129, 287),
    2842702200: (532, 126, 285),
    2839734373: (273, 128, 281),
    2836766546: (282, 256, 270),
    2833864255: (558, 128, 534),
    2830896428: (291, 140, 285),
    2827928601: (292, 141, 279),
    2825026310: (278, 137, 279),
    2822058483: (260, 138, 285),
    2819090656: (576, 132, 292),
    2816122829: (584, 270, 262),
    2813220538: (264, 141, 271),
    2810252711: (279, 132, 576),
    2807284884: (584, 129, 284),
    2804382593: (286, 135, 275),
}

if __name__ == '__main__':
    print('FFX HD PC manip tool')
    while True:
        main()
