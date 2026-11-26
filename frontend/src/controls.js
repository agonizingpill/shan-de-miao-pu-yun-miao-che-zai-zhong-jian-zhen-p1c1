import {awaitCompute, request} from './api.js';
import {el, display} from './dom.js';
import {COMPUTE_STATES, evidence} from './store.js';
import {status} from './widgets.js';

const fallback = field => field.kind === 'token' ? evidence.get() : field.initial;
function input(field) {
  if (field.kind === 'bool') return el('select', {name:field.name},
    el('option',{value:'true', selected:fallback(field) === true ? '' : undefined},'是'),
    el('option',{value:'false', selected:fallback(field) === false ? '' : undefined},'否'));
  if (field.kind === 'json') return el('textarea', {name:field.name, required:''}, JSON.stringify(fallback(field), null, 2));
  const numeric = ['int','float'].includes(field.kind);
  return el('input',{name:field.name, required:field.required === false ? undefined : '', type:numeric ? 'number' : 'text',
    step:field.kind === 'float' ? 'any' : undefined, value:fallback(field) ?? ''});
}
function parse(form, fields) {
  const data = new FormData(form);
  return Object.fromEntries(fields.map(field => {
    const raw = data.get(field.name);
    if ((raw === '' || raw === null) && field.required === false) return [field.name, null];
    const convert = ['int','float'].includes(field.kind) ? Number :
      ['bool','json'].includes(field.kind) ? JSON.parse : String;
    return [field.name, convert(raw)];
  }));
}
export function actionForm(action, refresh) {
  const notice = status('');
  const button = el('button', {type:'submit'}, action.label);
  const form = el('form', {class:'action', id:action.name},
    el('h3',{},action.label), el('p',{},action.help),
    el('div',{class:'fields'},action.fields.map(field => el('label',{},
      el('span',{},field.label), input(field)))),
    button, notice);
  form.addEventListener('submit',async event => {
    event.preventDefault();
    button.disabled = true;
    notice.className = 'status';
    try {
      const data = await request(action.path, parse(form, action.fields));
      if (data.token && data.status === 'queued') {
        evidence.save(data.token);
        const result = await awaitCompute(data.token, current => {
          notice.textContent = COMPUTE_STATES[current.status] || current.status;
        });
        if (result.status === 'rejected') throw new Error(result.detail);
        notice.textContent = '任务 ' + data.token + ' · ' + display(result.result);
      } else {
        notice.textContent = action.success + ' · ' + display(data.code ?? data.status);
      }
      notice.classList.add('ok');
      await refresh();
    } catch (error) {
      const rebaseToken = error.payload?.token && error.status === 409 ? error.payload.token : null;
      if (rebaseToken) {
        try {
          evidence.save(rebaseToken);
          const result = await awaitCompute(rebaseToken, current => {
            notice.textContent = (error.message || '候选已按现行建议重算') + '；' + (COMPUTE_STATES[current.status] || current.status);
          });
          if (result.status === 'rejected') throw new Error(result.detail);
          notice.textContent = (error.message || '候选已按现行建议重算') + '；新试算 ' + display(result.result);
          notice.classList.add('ok');
          await refresh();
          return;
        } catch (rebaseError) {
          notice.textContent = error.message + '；重算查询：' + rebaseError.message;
        }
      } else {
        notice.textContent = error.message;
      }
      notice.classList.add('error');
    } finally { button.disabled = false; }
  });
  return form;
}
