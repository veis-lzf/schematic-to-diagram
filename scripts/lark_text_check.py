#!/usr/bin/env python3
"""Check pairwise text-node bounding-box overlaps in a Feishu whiteboard export."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def load_nodes(path: Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("data"), dict):
            if "nodes" in data["data"]:
                return data["data"]["nodes"]
            if isinstance(data["data"].get("result"), dict) and "nodes" in data["data"]["result"]:
                return data["data"]["result"]["nodes"]
        if "nodes" in data:
            return data["nodes"]
    if isinstance(data, list):
        return data
    raise SystemExit("no nodes array found")


def overlaps(path: Path):
    nodes=load_nodes(path)
    texts=[]
    for n in nodes:
        if n.get("type")!="text_shape":
            continue
        txt=(n.get("text") or {}).get("text","")
        if not str(txt).strip():
            continue
        x=float(n.get("x",0) or 0); y=float(n.get("y",0) or 0)
        w=float(n.get("width",0) or 0); h=float(n.get("height",0) or 0)
        if w<=0 or h<=0:
            continue
        texts.append((n.get("id"),x,y,x+w,y+h,str(txt)))
    result=[]
    for i in range(len(texts)):
        for j in range(i+1,len(texts)):
            a,b=texts[i],texts[j]
            ix=min(a[3],b[3])-max(a[1],b[1])
            iy=min(a[4],b[4])-max(a[2],b[2])
            if ix>0 and iy>0:
                result.append({"a":a[0],"b":b[0],"overlap_x":round(ix,2),"overlap_y":round(iy,2),"a_text":a[5][:80],"b_text":b[5][:80]})
    return texts,result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("json_file",type=Path)
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    texts,result=overlaps(args.json_file)
    if args.json:
        print(json.dumps({"ok":not result,"texts":len(texts),"overlaps":len(result),"pairs":result},ensure_ascii=False,indent=2))
    else:
        print(f"text bbox check: {'clean' if not result else 'FAILED'} | texts={len(texts)} overlaps={len(result)}")
        for p in result:
            print(f"  ! {p['a']} x {p['b']} overlap={p['overlap_x']}x{p['overlap_y']}px")
    return 0 if not result else 1


if __name__=="__main__":
    sys.exit(main())
