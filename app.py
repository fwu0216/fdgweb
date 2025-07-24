import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

# 处理 HEAD 请求，避免 Render 触发 500 错误
@app.before_request
def handle_head_requests():
    if request.method == "HEAD":
        return "", 200

# 衰减计算公式
def decay_correction(dose, elapsed_minutes, half_life=109.7):
    return dose * (2 ** (elapsed_minutes / half_life))

def calculate_batches(weights, coeff=0.15, interval=30,
                      batch1_max=8, batch2_max=6, batch3_max=3,
                      enable_batch2=True, enable_batch3=True):
    """
    根据输入的体重列表计算三批F18-FDG分装剂量
    """
    results = []
    batches = []
    start_time = datetime.strptime("07:00", "%H:%M")

    idx = 0
    for batch_name, limit, enabled in [("第一批", batch1_max, True),
                                       ("第二批", batch2_max, enable_batch2),
                                       ("第三批", batch3_max, enable_batch3)]:
        if not enabled:
            continue
        batch_weights = weights[idx: idx+limit]
        idx += limit
        batch_results = []

        for i, w in enumerate(batch_weights, start=1):
            injection_time = start_time + timedelta(minutes=(i-1)*interval)
            planned_dose = round(w * coeff, 2)
            elapsed = (injection_time - start_time).total_seconds()/60
            dispense_dose = round(decay_correction(planned_dose, elapsed), 2)
            batch_results.append({
                "批次": batch_name,
                "编号": i,
                "体重(kg)": w,
                "注射时间": injection_time.strftime("%H:%M"),
                "分装时间": "07:00",
                "分装剂量(mCi)": dispense_dose
            })
        batches.append((batch_name, batch_results))
        results.extend(batch_results)

    return batches, results

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    batches = []
    error_msg = ""

    if request.method == "POST":
        try:
            coeff = float(request.form.get("coeff", "0.15") or 0.15)

            # 获取所有体重输入（动态字段）
            weights = []
            for key in request.form:
                if key.startswith("weight"):
                    val = request.form[key].strip()
                    if val:
                        weights.append(float(val))

            # 获取批次设置
            batch1_max = int(request.form.get("batch1_max", 8))
            enable_batch2 = "enable_batch2" in request.form
            batch2_max = int(request.form.get("batch2_max", 6)) if enable_batch2 else 0
            enable_batch3 = "enable_batch3" in request.form
            batch3_max = int(request.form.get("batch3_max", 3)) if enable_batch3 else 0

            if not weights:
                error_msg = "错误: 请至少输入一个有效的体重（数字）"
            else:
                batches, results = calculate_batches(weights, coeff,
                                                     batch1_max=batch1_max,
                                                     batch2_max=batch2_max,
                                                     batch3_max=batch3_max,
                                                     enable_batch2=enable_batch2,
                                                     enable_batch3=enable_batch3)
        except ValueError:
            error_msg = "错误: 输入的内容包含无效数字，请检查。"

    # 生成初始的 weight 字段（3个），支持动态添加
    weight_fields = ["" for _ in range(3)]

    return render_template("index.html",
                           results=results,
                           batches=batches,
                           weight_fields=weight_fields,
                           error_msg=error_msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
