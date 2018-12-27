# main.py -- put your code here!

# Astrtia Clock
# ver-0.7  2018-dec-25
# @ludwig_em

import pyb
import micropython

# Emergency exception buffer (Debug)
micropython.alloc_emergency_exception_buf(200)

L_RED = micropython.const(1)   # Red LED
L_GREEN = micropython.const(2)   # Green LED
L_ORANGE = micropython.const(3)   # Orange LED
L_BLUE = micropython.const(4)   # Blue LED


# 1秒Lチカ
# （ベンチマーク）
tim = pyb.Timer(1)
tim.init(freq=2)
tim.callback(lambda t: pyb.LED(L_RED).toggle())

# 初期化　メインクロック
# ストライプ間の時間間隔
# 96分割 45秒 （72分 / 96 = 4320秒 / 96 = 45秒）
# priscaler により 1 period は 0.5 mSec
tim_clock = pyb.Timer(2)
tim_clock.init(prescaler=41999, period=90000)

# 初期化　ステッピングモーター1Step駆動時間間隔
# （時計盤回転スピード）
tim_r = pyb.Timer(4)
tim_r.init(freq=13)      # 駆動周期
#tim_r.init(freq=50)      # 駆動周期(デモ用)

# 初期化　フォトセンサー検知周期
tim_s = pyb.Timer(6)
tim_s.init(freq=20)      # 検知周期  


# 初期化　ステッピングモーター駆動 GPIO 出力
ph1 = pyb.Pin('X4',pyb.Pin.OUT_PP)
ph2 = pyb.Pin('X3',pyb.Pin.OUT_PP)
ph3 = pyb.Pin('X2',pyb.Pin.OUT_PP)
ph4 = pyb.Pin('X1',pyb.Pin.OUT_PP)

# 初期化　アナログ入力
# （フォトセンサー）
pr_sig = pyb.ADC('X22')

# 初期化　時計盤回転フラグ等
rotate_f = True      # motor rotate flag
FORWARD = micropython.const(+1)
REVERSE = micropython.const(-1)
rot_dir = FORWARD   # rotate direction

# メインクロック
def mainclock():
  global rotate_f
  rotate_f = True         # Ratate motor
  pyb.LED(L_ORANGE).toggle()

tim_clock.callback(lambda t:mainclock())

# ステッピングモーター1Step駆動
#  1-2相励磁で8状態
def rotate():
  state = 0
  q = 0
  def rotatestate():
    nonlocal state
    nonlocal q
    if rotate_f == True:
      if state == 0:
        ph1.high()
        ph2.low()
        ph3.low()
        ph4.low()
        q += rot_dir
      elif state == 1:
        ph1.high()
        ph2.high()
        ph3.low()
        ph4.low()
        q += rot_dir
      elif state == 2:
        ph1.low()
        ph2.high()
        ph3.low()
        ph4.low()
        q += rot_dir
      elif state == 3:
        ph1.low()
        ph2.high()
        ph3.high()
        ph4.low()
        q += rot_dir
      elif state == 4:
        ph1.low()
        ph2.low()
        ph3.high()
        ph4.low()
        q += rot_dir
      elif state == 5:
        ph1.low()
        ph2.low()
        ph3.high()
        ph4.high()
        q += rot_dir
      elif state == 6:
        ph1.low()
        ph2.low()
        ph3.low()
        ph4.high()
        q += rot_dir
      elif state == 7:
        ph1.high()
        ph2.low()
        ph3.low()
        ph4.high()
        q += rot_dir
      else:
        q = 0
      q %= 8
      state = q
  return rotatestate

r = rotate()
tim_r.callback(lambda t:r())


# フォトセンサーの処理
# ストライプが切り替わったらモーターを止める
# 移動平均をかけてストライプ判別を確実にしている
WHITE = micropython.const(True)
BLACK = micropython.const(False)
stripe = BLACK            # 現在のストライプ色
befstripe = BLACK         # 一つ過去のストライプ色
MAVRNUM = micropython.const(10)   # 移動平均の深さ
THRESHOLD = micropython.const(1400)  # ストライプ判定閾値
mavrbuf = [0] * MAVRNUM   # 移動平均バッファー
cnt = 0                   # 移動平均カウンター
def sadc():
  global stripe
  global befstripe
  global rotate_f
  #global mavrbuf
  global cnt
  av = 0
  mavrbuf[cnt] = pr_sig.read()     # フォトセンサー値入力
  #print (mavrbuf[cnt])    # (Adjustment)pr_sig表示 THRESHOLD決定のため
  cnt += 1
  cnt %= MAVRNUM
  av = 0
  for i in range(MAVRNUM):      # 移動平均計算
    av += mavrbuf[i]
  #print (av)
  if av < THRESHOLD * MAVRNUM:    # コールバック内で割り算（浮動小数点）は利用できないから
    pyb.LED(L_BLUE).off()
    stripe = BLACK
  else:
    pyb.LED(L_BLUE).on()
    stripe = WHITE
  if stripe != befstripe :
    rotate_f = False        # ストライプが切り替わったらモーター停止
    befstripe = stripe

tim_s.callback(lambda t:sadc())
