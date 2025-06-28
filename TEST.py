from flask import Flask, render_template, request, jsonify
import math
import os
import google.generativeai as genai

app = Flask(__name__)

# Set your Gemini API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyDJPdvqPCpYOIGNwq9HmusF0tc8hhm8ys0"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


def get_llm_explanation(prompt_text):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"LLM Error: {str(e)}"


def problem_one(BW, quantizer_bits, Rs, Rc):
    fs = 2 * BW
    quantizer_levels = 2 ** quantizer_bits
    quantizer_out_bit_rate = quantizer_bits * fs
    source_encoder_out_bit_rate = quantizer_out_bit_rate * Rs
    channel_encoder_out_bit_rate = source_encoder_out_bit_rate / Rc
    interleaver_out_bit_rate = channel_encoder_out_bit_rate

    explanation = f"""
- Sampling frequency (fs) = 2 × BW = {fs} kHz
- Quantizer levels = 2^{quantizer_bits} = {quantizer_levels}
- Quantizer output bitrate = {quantizer_bits} × fs = {quantizer_out_bit_rate:.1f} kbps
- Source encoder output bitrate = quantizer bitrate × Rs = {source_encoder_out_bit_rate:.1f} kbps
- Channel encoder output bitrate = source encoder bitrate / Rc = {channel_encoder_out_bit_rate:.1f} kbps
- Interleaver output bitrate = {interleaver_out_bit_rate:.1f} kbps
"""

    return {
        "fs": fs,
        "quantizer_levels": quantizer_levels,
        "quantizer_out": quantizer_out_bit_rate,
        "source_out": source_encoder_out_bit_rate,
        "channel_out": channel_encoder_out_bit_rate,
        "interleaver_out": interleaver_out_bit_rate,
        "explanation": explanation
    }


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/problem1', methods=['GET', 'POST'])
def problem1():
    if request.method == 'POST':
        try:
            BW = float(request.form['bandwidth'])
            quantizer_bits = int(request.form['quantizer_bits'])
            Rs = float(request.form['source_rate'])
            Rc = float(request.form['channel_rate'])

            result = problem_one(BW, quantizer_bits, Rs, Rc)

            prompt = f"""Please explain in a simple and technical way the following wireless bitrate results:
{result['explanation']}
Include: what each number means, why it's important, and how it's applied in real systems."""
            result["llm_explanation"] = get_llm_explanation(prompt)

            return render_template("problem1.html", result=result)
        except Exception as e:
            return render_template("problem1.html", error=str(e))

    return render_template("problem1.html")


def problem_two(n_sub, sub_spacing, bits_per_symbol, symbols_per_slot):
    bw_per_re = bits_per_symbol
    rate_symbol = n_sub * bw_per_re
    rate_block = rate_symbol * symbols_per_slot
    spectral_eff = rate_symbol / (n_sub * sub_spacing)

    explanation = (
        f"- Bits per Resource Element = {bw_per_re}\n"
        f"- Bits per OFDM Symbol = n_sub × bits/RE = {rate_symbol}\n"
        f"- Bits per Resource Block = OFDM Symbol × Symbols/Slot = {rate_block}\n"
        f"- Spectral Efficiency = Rate per OFDM symbol / (n_sub × Subcarrier Spacing) = {spectral_eff:.3f} b/Hz"
    )

    return dict(
        bits_re=bw_per_re,
        bits_sym=rate_symbol,
        bits_rb=rate_block,
        spectral_eff=spectral_eff,
        explanation=explanation
    )


@app.route('/problem2', methods=['GET', 'POST'])
def problem2():
    if request.method == 'POST':
        n_sub = int(request.form['n_sub'])
        sub_spacing = float(request.form['spacing'])
        bits_per_symbol = int(request.form['bps'])
        symbols_per_slot = int(request.form['sym_slot'])
        result = problem_two(n_sub, sub_spacing, bits_per_symbol, symbols_per_slot)

        prompt = f"""Explain the following OFDM parameters and their significance:
{result['explanation']}
Make it technical but simple."""
        result["llm_explanation"] = get_llm_explanation(prompt)

        return render_template('problem2.html', result=result)
    return render_template('problem2.html')


def problem_three(Pt, Gt, Gr, d_km, f_mhz, losses=0):
    fspl = 32.45 + 20 * math.log10(d_km) + 20 * math.log10(f_mhz)
    Pr = Pt + Gt + Gr - fspl - losses

    explanation = (
        f"- Pt = {Pt} dBm\n"
        f"- Gt = {Gt} dBi\n"
        f"- Gr = {Gr} dBi\n"
        f"- d = {d_km} km, f = {f_mhz} MHz, Losses = {losses} dB\n"
        f"- FSPL = 32.45 + 20log(d) + 20log(f) = {fspl:.2f} dB\n"
        f"- Received Power Pr = Pt + Gt + Gr - FSPL - Losses = {Pr:.2f} dBm"
    )

    return {
        "fspl": round(fspl, 2),
        "received_power": round(Pr, 2),
        "explanation": explanation
    }


@app.route('/problem3', methods=['GET', 'POST'])
def problem3():
    if request.method == 'POST':
        Pt = float(request.form['Pt'])
        Gt = float(request.form['Gt'])
        Gr = float(request.form['Gr'])
        d_km = float(request.form['d_km'])
        f_mhz = float(request.form['f_mhz'])
        losses = float(request.form.get('losses', 0))
        result = problem_three(Pt, Gt, Gr, d_km, f_mhz, losses)

        prompt = f"""Explain the received power calculation with FSPL model below:
{result['explanation']}
Explain each variable and the formula used in practical systems."""
        result["llm_explanation"] = get_llm_explanation(prompt)

        return render_template('problem3.html', result=result)
    return render_template('problem3.html')


def problem_four(model, freq, dist, ht, hr):
    explanation = ""
    if model == "FSPL":
        L = 32.45 + 20 * math.log10(dist) + 20 * math.log10(freq)
        explanation = f"FSPL = 32.45 + 20log({dist}) + 20log({freq}) = {L:.2f} dB"
    elif model == "Hata":
        a_hr = (1.1 * math.log10(freq) - 0.7) * hr - (1.56 * math.log10(freq) - 0.8)
        L = 69.55 + 26.16 * math.log10(freq) - 13.82 * math.log10(ht) - a_hr + (44.9 - 6.55 * math.log10(ht)) * math.log10(dist)
        explanation = f"Hata = 69.55 + 26.16log({freq}) - 13.82log({ht}) - a(hr) + (44.9 - 6.55log({ht}))log({dist}) = {L:.2f} dB"
    else:
        return {"error": "Invalid model selected"}

    return {
        "model": model,
        "path_loss": round(L, 2),
        "explanation": explanation
    }


@app.route("/problem4", methods=["GET", "POST"])
def problem4():
    if request.method == "POST":
        model = request.form["model"]
        freq = float(request.form["freq"])
        dist = float(request.form["dist"])
        ht = float(request.form["ht"])
        hr = float(request.form["hr"])
        result = problem_four(model, freq, dist, ht, hr)

        prompt = f"""Explain the path loss calculation using {model} model:
{result['explanation']}
Make it clear, simple, and practical."""
        result["llm_explanation"] = get_llm_explanation(prompt)

        return render_template("problem4.html", result=result)
    return render_template("problem4.html")


if __name__ == '__main__':
    app.run(debug=True)
