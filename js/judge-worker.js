/* Web Worker: выполняет Python-код ученика в Pyodide.
   Сообщения: {id, type: 'init'} | {id, type: 'run', code, input} | {id, type: 'check', fn, inp, out, exp, checkers} */
importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js');

let py = null;

const HARNESS = `
import sys, io, time, traceback
sys.setrecursionlimit(10000)
def __oly_run(src, inp):
    real_in, real_out, real_err = sys.stdin, sys.stdout, sys.stderr
    sys.stdin = io.TextIOWrapper(io.BytesIO(inp.encode()), encoding='utf-8')
    out = io.StringIO()
    err = io.StringIO()
    sys.stdout = out
    sys.stderr = err
    msg = ''
    t0 = time.perf_counter()
    try:
        exec(compile(src, 'solution.py', 'exec'), {'__name__': '__main__'})
    except SystemExit:
        pass
    except BaseException:
        tb = traceback.format_exc().splitlines()
        msg = '\\n'.join(tb[-6:])
    finally:
        sys.stdin, sys.stdout, sys.stderr = real_in, real_out, real_err
    return [out.getvalue(), msg or err.getvalue()[-2000:], time.perf_counter() - t0]
`;

async function init() {
  if (py) return;
  py = await loadPyodide();
  py.runPython(HARNESS);
}

self.onmessage = async (e) => {
  const m = e.data;
  try {
    await init();
    if (m.type === 'init') {
      self.postMessage({ id: m.id, ok: true });
    } else if (m.type === 'run') {
      // numpy и другие пакеты Pyodide подгружаются по import в коде
      await py.loadPackagesFromImports(m.code);
      const fn = py.globals.get('__oly_run');
      const res = fn(m.code, m.input);
      const [out, err, time] = res.toJs();
      res.destroy(); fn.destroy();
      self.postMessage({ id: m.id, ok: true, out, err, time });
    } else if (m.type === 'check') {
      if (!py.globals.get('check_target_mst')) py.runPython(m.checkers);
      const fn = py.globals.get(m.fn);
      const res = fn(m.inp, m.out, m.exp);
      const [good, msg] = res.toJs();
      res.destroy(); fn.destroy();
      self.postMessage({ id: m.id, ok: true, good, msg });
    }
  } catch (err) {
    self.postMessage({ id: m.id, ok: false, error: String(err && err.message || err) });
  }
};
