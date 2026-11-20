import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from samples import SAMPLES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(pid, inp, timeout=30):
    r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'sol', pid + '.py')],
                       input=inp, capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout


if __name__ == '__main__':
    bad = 0
    for pid, tests in SAMPLES.items():
        if not os.path.exists(os.path.join(ROOT, 'sol', pid + '.py')):
            print(f'{pid:12s} — нет решения')
            continue
        for i, (inp, exp) in enumerate(tests, 1):
            got = run(pid, inp).split()
            want = exp.split()
            if pid == 'nauryz':
                ok = got[:1] == want[:1]
            elif pid == 'target-mst':
                ok = got[:1] == want[:1]
            else:
                ok = got == want
            print(f'{pid:12s} #{i}: {"OK" if ok else "FAIL"}' + ('' if ok else f'  got={got} want={want}'))
            bad += not ok
    print('ошибок:', bad)
