rig_snapshot() {
  local stage_dir="$1" label="$2"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$stage_dir/snapshot-$label.timestamp.txt"
  ss -tlnp > "$stage_dir/listeners-$label.txt"
  sudo -n iptables -S > "$stage_dir/iptables-$label.rules.txt"
  sudo -n ip6tables -S > "$stage_dir/ip6tables-$label.rules.txt"
  sudo -n iptables -L -n -v --line-numbers > "$stage_dir/iptables-$label.txt"
  sudo -n ip6tables -L -n -v --line-numbers > "$stage_dir/ip6tables-$label.txt"
}
rig_check_core() {
  python3 - "$1" "$2" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);label=sys.argv[2]
text=(p/f'listeners-{label}.txt').read_text()
rows=text.splitlines()[1:]
checks={}
for port,pid,name in [(8000,62427,'api'),(8799,62991,'collector'),(4873,66203,'verdaccio')]:
    bound=[r for r in rows if r.split()[3].rsplit(':',1)[-1]==str(port)]
    checks[name+'_loopback_original_pid']=len(bound)==1 and bound[0].split()[3]==f'127.0.0.1:{port}' and f'pid={pid},' in bound[0]
engine=[r for r in rows if 'VLLM::EngineCor' in r]
checks['enginecore_ports_unchanged']=len(engine)==7 and all('pid=62603,' in r for r in engine) and sorted(int(r.split()[3].rsplit(':',1)[-1]) for r in engine)==[32919,34157,36881,37405,39009,45681,55253]
v4=[r for r in (p/f'iptables-{label}.rules.txt').read_text().splitlines() if r.startswith('-A INPUT')]
v6=[r for r in (p/f'ip6tables-{label}.rules.txt').read_text().splitlines() if r.startswith('-A INPUT')]
checks['enginecore_ipv4_first_rule']=bool(v4) and v4[0]=='-A INPUT ! -i lo -p tcp -m multiport --dports 32919,34157,36881,37405,39009,45681,55253 -j DROP'
checks['enginecore_ipv6_first_rule']=bool(v6) and v6[0]=='-A INPUT ! -i lo -p tcp -m tcp --dport 55253 -j DROP'
record={'run':0,'snapshot':label,'checks':checks,'passed':all(checks.values())}
(p/f'network-check-{label}.json').write_text(json.dumps(record,indent=2)+'\n')
if not record['passed']:print(json.dumps(record,indent=2));raise SystemExit(1)
PY
}
