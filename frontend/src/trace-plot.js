import {request} from './api.js';
import {el} from './dom.js';

const svgNamespace = 'http://www.w3.org/2000/svg';

function svg(name, attributes, text) {
  const node = document.createElementNS(svgNamespace, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text) node.textContent = text;
  return node;
}

function chart(rows, route) {
  const points = rows.filter((row) => row.route === route && row.verified)
    .sort((a, b) => a.load_kg - b.load_kg);
  const graph = svg('svg', {viewBox:'0 0 490 210', role:'img', class:'plot',
    'aria-label':route + ' 台架载重与振动观测散点'});
  const width = 400, height = 158, left = 48, base = 178;
  const maxX = Math.max(100, ...points.map((row) => row.load_kg));
  const maxY = Math.max(1, ...points.map((row) => row.rms));
  for (const f of [0,.25,.5,.75,1]) {
    const y = base - f * height;
    graph.append(svg('line',{x1:left,y1:y,x2:left+width,y2:y}));
    graph.append(svg('text',{x:5,y:y+4},(f * maxY).toFixed(2)));
    graph.append(svg('text',{x:left+f*width-7,y:198},String(Math.round(f*maxX))));
  }
  for (const row of points) {
    const point = svg('circle',{cx:left+row.load_kg/maxX*width,cy:base-row.rms/maxY*height,r:3.5});
    point.append(svg('title',{},row.code+' · '+row.load_kg+' kg · RMS '+row.rms));
    graph.append(point);
  }
  return graph;
}

export async function tracePlot(root) {
  const rows = await request('/road_observations');
  const panel = el('figure',{class:'trail-trends'},
    el('figcaption',{},'路线台架散点 · 载重 kg 与 RMS'));
  const select = el('select',{'aria-label':'比较路线'},
    [...new Set(rows.map((row) => row.route))].map((route) => el('option',{value:route},route)));
  const plot = el('div',{});
  function render() { plot.replaceChildren(chart(rows, select.value)); }
  select.addEventListener('change',render);
  panel.append(select, plot, el('small',{},'横轴为苗盘测试载重，纵轴为台架记录的 RMS，仅显示已复核数据。'));
  render();
  root.querySelector('.ledger')?.before(panel);
}
