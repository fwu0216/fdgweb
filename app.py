from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)

def decay_correction(dose, elapsed_minutes, half_life=109.7):
    """计算放射性衰减校正后的剂量"""
    return dose * (2 ** (elapsed_minutes / half_life))

def calculate_batches(weights, coeff=0.15, interval=30,
                      batch1_max=8, batch2_max=6, batch3_max=3,
                      enable_batch2=True, enable_batch3=True):
    """根据患者体重和批次设置计算每位患者的分装剂量"""
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
    sms_text = ""

    # 默认三批短信配置
    default_batches = [
        {"enabled": True, "dose": 200, "scale_time": "9:00", "arrive_time": "8:10"},
        {"enabled": True, "dose": 110, "scale_time": "11:20", "arrive_time": "10:30"},
        {"enabled": True, "dose": 30,  "scale_time": "13:20", "arrive_time": "13:00"}
    ]

    if request.method == "POST":
        form_type = request.form.get("form_type", "calc")
        try:
            if form_type == "calc":
                coeff = float(request.form.get("coeff", 0.15))
                # 收集所有动态体重
                weights = []
                for key, value in request.form.items():
                    if key.startswith("weight") and value.strip():
                        try:
                            weights.append(float(value))
                        except ValueError:
                            continue
                if not weights:
                    raise ValueError("请至少输入一个有效的体重（数字）")

                batch1_max = int(request.form.get("batch1_max", 8))
                enable_batch2 = request.form.get("enable_batch2") == "on"
                batch2_max = int(request.form.get("batch2_max", 6)) if enable_batch2 else 0
                enable_batch3 = request.form.get("enable_batch3") == "on"
                batch3_max = int(request.form.get("batch3_max", 3)) if enable_batch3 else 0

                total_requested = batch1_max + (batch2_max if enable_batch2 else 0) + (batch3_max if enable_batch3 else 0)
                if total_requested > len(weights):
                    weights = weights[:total_requested]

                batches, results = calculate_batches(weights, coeff,
                                                      batch1_max=batch1_max,
                                                      batch2_max=batch2_max,
                                                      batch3_max=batch3_max,
                                                      enable_batch2=enable_batch2,
                                                      enable_batch3=enable_batch3)

            elif form_type == "sms":
                # 生成短信内容
                sms_batches = []
                for i in range(1, 4):
                    enabled = request.form.get(f"enable_batch{i}") == "on"
                    dose = request.form.get(f"dose{i}", "0")
                    scale = request.form.get(f"scale{i}", "")
                    arrive = request.form.get(f"arrive{i}", "")
                    if enabled:
                        sms_batches.append(f"第{i}批需要FDG {dose}mCi，刻度到{scale}\n{arrive}左右送达")
                if sms_batches:
                    sms_text = "FDG\n" + "\n".join(sms_batches)

        except Exception as e:
            error_msg = f"错误: {str(e)}"

    # 渲染页面
    return render_template("index.html",
                           results=results, batches=batches,
                           error_msg=error_msg, sms_text=sms_text,
                           default_batches=default_batches)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
