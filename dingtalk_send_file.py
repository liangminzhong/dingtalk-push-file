#!/usr/bin/env python3
"""
钉钉单聊发送文件（sampleFile）通用脚本
=====================================
钉钉不支持直接发 .html（errcode 40005），复杂报告请先转 PDF：
  chromium-browser --headless --no-sandbox --disable-gpu \
    --print-to-pdf=out.pdf --print-to-pdf-no-header "file:///path/in.html"

用法：
  python3 dingtalk_send_file.py /path/report.pdf --profile default \
      --user YOUR_USER_ID --display-name "台州行程单.pdf"
"""
import os, sys, json, argparse, glob

def parse_env(path):
    env = {}
    try:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except OSError:
        pass
    return env

def find_creds(profile=None):
    cid = os.environ.get("DINGTALK_CLIENT_ID", "")
    csec = os.environ.get("DINGTALK_CLIENT_SECRET", "")
    if cid and csec:
        return cid, csec
    cands = []
    if profile:
        cands.append(os.path.expanduser(f"~/.hermes/profiles/{profile}/.env"))
    cands += glob.glob(os.path.expanduser("~/.hermes/profiles/*/.env"))
    cands.append(os.path.expanduser("~/.hermes/.env"))
    for p in cands:
        e = parse_env(p)
        if e.get("DINGTALK_CLIENT_ID") and e.get("DINGTALK_CLIENT_SECRET"):
            return e["DINGTALK_CLIENT_ID"], e["DINGTALK_CLIENT_SECRET"]
    return "", ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="要发送的文件路径（建议 PDF）")
    ap.add_argument("--profile", default="default")
    ap.add_argument("--user", default=os.environ.get("DINGTALK_NOTIFY_USERID", "YOUR_USER_ID"))
    ap.add_argument("--display-name", help="钉钉里显示的文件名")
    args = ap.parse_args()

    import requests
    if not os.path.isfile(args.file):
        print(f"❌ 文件不存在: {args.file}", file=sys.stderr); sys.exit(1)

    cid, csec = find_creds(args.profile)
    if not cid:
        print("❌ 缺少钉钉凭证", file=sys.stderr); sys.exit(1)

    tok = requests.get("https://oapi.dingtalk.com/gettoken",
                       params={"appkey": cid, "appsecret": csec}, timeout=15).json()
    if tok.get("errcode") != 0:
        print(f"❌ token 失败: {tok}", file=sys.stderr); sys.exit(1)
    token = tok["access_token"]

    fname = args.display_name or os.path.basename(args.file)
    with open(args.file, "rb") as f:
        up = requests.post(f"https://oapi.dingtalk.com/media/upload?access_token={token}&type=file",
                           files={"media": (fname, f)}, timeout=60).json()
    media_id = up.get("media_id")
    if not media_id:
        print(f"❌ 上传失败: {up}（提示：.html 不被支持，请先转 PDF）", file=sys.stderr); sys.exit(1)

    payload = {
        "robotCode": cid,
        "userIds": [args.user],
        "msgKey": "sampleFile",
        "msgParam": json.dumps({"mediaId": media_id, "fileName": fname}, ensure_ascii=False),
    }
    r = requests.post("https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend",
                      headers={"Content-Type": "application/json",
                               "x-acs-dingtalk-access-token": token},
                      json=payload, timeout=30).json()
    if r.get("processQueryKey") and not r.get("invalidStaffIdList"):
        print(f"✅ 文件已推送: {fname}")
    else:
        print(f"❌ 发送失败: {json.dumps(r, ensure_ascii=False)}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
