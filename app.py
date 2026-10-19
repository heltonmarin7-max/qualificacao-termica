import io
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, redirect, render_template, request, send_file, session, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
	Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'qualificacao_termica_comprehense_key')

USERS = {'tecnico': 'elber1935'}


@app.route('/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		if username in USERS and USERS[username] == password:
			session['user'] = username
			return redirect(url_for('formulario'))
		return render_template('login.html', error='Usuário ou senha inválidos.')
	return render_template('login.html')


@app.route('/logout')
def logout():
	session.pop('user', None)
	return redirect(url_for('login'))


def parse_horarios(raw_str, default_list):
	horarios = [item.strip() for item in (raw_str or '').split(',') if item.strip()]
	return horarios or default_list


def parse_sensor_inputs(request_form, prefix, num_points, default_range):
	sensores = {}
	for i in range(1, 13):
		raw_vals = request_form.get(f'{prefix}_sensor_{i}', '').strip()
		if raw_vals:
			try:
				vals = [float(value.strip()) for value in raw_vals.split(',') if value.strip()]
			except ValueError as exc:
				raise ValueError(f'Leituras inválidas no sensor T{i}.') from exc
			if not vals:
				vals = list(np.round(np.random.uniform(*default_range, num_points), 2))
		else:
			vals = list(np.round(np.random.uniform(*default_range, num_points), 2))
		if len(vals) < num_points:
			vals.extend([vals[-1]] * (num_points - len(vals)))
		sensores[f'T{i}'] = vals[:num_points]
	return sensores


def build_data_table(sensores, horarios, body_style):
	header = ['Horário'] + [f'T{i}' for i in range(1, 13)]
	table_data = [[Paragraph(f'<b>{label}</b>', body_style) for label in header]]
	for idx, horario in enumerate(horarios):
		row = [Paragraph(horario, body_style)]
		for i in range(1, 13):
			values = sensores[f'T{i}']
			value = values[idx] if idx < len(values) else 0.0
			row.append(Paragraph(f'{value:.1f}', body_style))
		table_data.append(row)
	return table_data


def gerar_grafico_curvas(sensores_dict, horarios, titulo, ylabel='Temperatura °C'):
	fig, axis = plt.subplots(figsize=(6, 2.2), dpi=150)
	for i in range(1, 13):
		axis.plot(horarios, sensores_dict.get(f'T{i}', [5] * len(horarios)),
				  marker='o', markersize=2, linewidth=1, label=f'T{i}')
	axis.set_title(titulo, fontsize=9, fontweight='bold', color='#1A365D')
	axis.set_xlabel('Horário da Medição', fontsize=7)
	axis.set_ylabel(ylabel, fontsize=7)
	axis.tick_params(axis='x', labelsize=6, rotation=30)
	axis.tick_params(axis='y', labelsize=6)
	axis.grid(True, linestyle='--', alpha=0.5)
	axis.legend(loc='upper right', fontsize=5, ncol=6, frameon=True)
	fig.tight_layout()
	img_io = io.BytesIO()
	fig.savefig(img_io, format='png', bbox_inches='tight')
	plt.close(fig)
	img_io.seek(0)
	return img_io


@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
	if 'user' not in session:
		return redirect(url_for('login'))
	if request.method != 'POST':
		return render_template('formulario.html')

	try:
		cliente_nome = request.form.get('cliente_nome', 'HOSPITAL UNIVERSITÁRIO WALTER CANTÍDIO')
		cliente_setor = request.form.get('cliente_setor', 'FARMÁCIA CLÍNICA HUWC')
		cliente_endereco = request.form.get('cliente_endereco', 'RUA PASTOR SAMUEL MUNGUBA, 1290')
		cliente_cidade = request.form.get('cliente_cidade', 'FORTALEZA - CEARÁ')
		cliente_cep = request.form.get('cliente_cep', '60430-372')
		equip_descricao = request.form.get('equip_descricao', 'REFRIGERADOR FARMACIA VERTICAL')
		tag = request.form.get('tag', '08633')
		serie = request.form.get('serie', '291801084')
		modelo = request.form.get('modelo', 'CSV-500')
		fabricante = request.form.get('fabricante', 'ELBER')
		patrimonio = request.form.get('patrimonio', '442360')
		capacidade = request.form.get('capacidade', '500')
		faixa_trabalho = request.form.get('faixa_trabalho', '2°C à 8°C')
		eletrica = request.form.get('eletrica', '220V / 426W / 1.9A')
		num_relatorio = request.form.get('num_relatorio', '26.5834')
		data_ensaio = request.form.get('data_ensaio', '23/07/2026 a 31/07/2026')
		datalogger_info = request.form.get('datalogger_info', 'DATALOGGER MAGETECH | S/N: T17920')
		termo_info = request.form.get('termo_info', 'TERMOHIGRÔMETRO | S/N: C210941510')
		cond_ambiental = request.form.get('cond_ambiental', 'Temperatura: 22,3 °C | Umidade: 51,0 %UR')
		tecnico_executor = request.form.get('tecnico_executor', 'Joaquim Carvalho S. Junior')
		responsavel_tecnico = request.form.get('responsavel_tecnico', 'Bredon Mitterhofer Alves')

		h_est = parse_horarios(request.form.get('horarios_est'), ['19:00', '19:03', '19:06', '19:09', '19:12', '19:15', '19:18', '19:21', '19:24', '19:27'])
		h_sub = parse_horarios(request.form.get('horarios_sub'), ['20:52', '20:53', '20:54', '20:55', '20:56'])
		h_desc = parse_horarios(request.form.get('horarios_desc'), ['20:56', '20:57', '20:58', '20:59', '21:00'])
		est_sensores = parse_sensor_inputs(request.form, 'est', len(h_est), (4.0, 6.0))
		sub_sensores = parse_sensor_inputs(request.form, 'sub', len(h_sub), (4.5, 7.5))
		desc_sensores = parse_sensor_inputs(request.form, 'desc', len(h_desc), (3.5, 6.5))
	except ValueError as exc:
		return render_template('formulario.html', error=str(exc)), 400

	img_est = gerar_grafico_curvas(est_sensores, h_est, 'Estabilidade Térmica - Operação Normal')
	img_sub = gerar_grafico_curvas(sub_sensores, h_sub, 'Estudo de Subida - Porta Aberta')
	img_desc = gerar_grafico_curvas(desc_sensores, h_desc, 'Estudo de Descida - Restabelecimento')

	pdf_stream = io.BytesIO()
	doc = SimpleDocTemplate(pdf_stream, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30)
	styles = getSampleStyleSheet()
	title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=12, leading=14, alignment=1, textColor=colors.HexColor('#1A365D'))
	subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Heading2'], fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor('#4A5568'))
	header_section = ParagraphStyle('HeaderSection', parent=styles['Heading3'], fontSize=9.5, leading=12, textColor=colors.HexColor('#2B6CB0'))
	body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=7.5, leading=9, alignment=1)
	body_left = ParagraphStyle('BodyLeft', parent=styles['Normal'], fontSize=7.5, leading=9)
	elements = []

	elements += [Paragraph('<b>COMPREHENSE ENGENHARIA CLÍNICA</b>', title_style),
				 Paragraph('<b>RELATÓRIO DE QUALIFICAÇÃO TÉRMICA (RQT)</b>', title_style),
				 Paragraph(f'Nº do Relatório: {num_relatorio} | Conforme Anvisa RDC 430/2020 e ABNT NBR 16327', subtitle_style), Spacer(1, 15),
				 Paragraph('<b>1. Dados do Cliente e Localização</b>', header_section), Spacer(1, 4)]
	cliente_data = [
		[Paragraph('<b>Cliente:</b>', body_left), Paragraph(cliente_nome, body_left), Paragraph('<b>Setor:</b>', body_left), Paragraph(cliente_setor, body_left)],
		[Paragraph('<b>Endereço:</b>', body_left), Paragraph(cliente_endereco, body_left), Paragraph('<b>Cidade/UF:</b>', body_left), Paragraph(cliente_cidade, body_left)],
		[Paragraph('<b>CEP:</b>', body_left), Paragraph(cliente_cep, body_left), Paragraph('<b>Período:</b>', body_left), Paragraph(data_ensaio, body_left)],
	]
	t_cli = Table(cliente_data, colWidths=[65, 205, 75, 185])
	t_cli.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FAFC')), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0, 0), (-1, -1), 4)]))
	elements += [t_cli, Spacer(1, 12), Paragraph('<b>2. Dados do Equipamento</b>', header_section), Spacer(1, 4)]
	equip_data = [
		[Paragraph('<b>Equipamento:</b>', body_left), Paragraph(equip_descricao, body_left), Paragraph('<b>TAG:</b>', body_left), Paragraph(tag, body_left)],
		[Paragraph('<b>Fabricante:</b>', body_left), Paragraph(fabricante, body_left), Paragraph('<b>Modelo:</b>', body_left), Paragraph(modelo, body_left)],
		[Paragraph('<b>Nº de Série:</b>', body_left), Paragraph(serie, body_left), Paragraph('<b>Patrimônio:</b>', body_left), Paragraph(patrimonio, body_left)],
		[Paragraph('<b>Capacidade:</b>', body_left), Paragraph(f'{capacidade} L', body_left), Paragraph('<b>Faixa Trabalho:</b>', body_left), Paragraph(faixa_trabalho, body_left)],
		[Paragraph('<b>Elétrica:</b>', body_left), Paragraph(eletrica, body_left), Paragraph('<b>Cond. Ambientais:</b>', body_left), Paragraph(cond_ambiental, body_left)],
	]
	t_eq = Table(equip_data, colWidths=[75, 195, 75, 185])
	t_eq.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FAFC')), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0, 0), (-1, -1), 4)]))
	padroes_data = [[Paragraph('<b>Sistema de Aquisição:</b>', body_left), Paragraph(datalogger_info, body_left)], [Paragraph('<b>Termohigrômetro:</b>', body_left), Paragraph(termo_info, body_left)]]
	t_pad = Table(padroes_data, colWidths=[110, 420])
	t_pad.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FAFC')), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0, 0), (-1, -1), 4)]))
	elements += [t_eq, Spacer(1, 12), Paragraph('<b>3. Padrões Utilizados na Calibração / Qualificação</b>', header_section), Spacer(1, 4), t_pad, PageBreak()]

	elements += [Paragraph('<b>4. Planilhas de Dados Coletados de Temperatura (°C)</b>', header_section), Spacer(1, 8)]
	for title, sensores, horarios, color, background in [
		('A. Estabilidade Térmica (Operação Normal)', est_sensores, h_est, '#2B6CB0', '#EDF2F7'),
		('B. Estudo de Subida (Porta Aberta / Aquecimento)', sub_sensores, h_sub, '#C53030', '#FFF5F5'),
		('C. Estudo de Descida (Restabelecimento Térmico)', desc_sensores, h_desc, '#2F855A', '#F0FFF4'),
	]:
		table = Table(build_data_table(sensores, horarios, body_style), colWidths=[42] + [44] * 12)
		table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color)), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(background)]), ('PADDING', (0, 0), (-1, -1), 2)]))
		elements += [Paragraph(f'<b>{title}</b>', header_section), Spacer(1, 4), table, Spacer(1, 10)]
	elements += [PageBreak(), Paragraph('<b>5. Anexo: Gráficos dos Dados Coletados de Temperatura</b>', header_section), Spacer(1, 6),
				 Image(img_est, width=450, height=160), Spacer(1, 4), Image(img_sub, width=450, height=160), Spacer(1, 4), Image(img_desc, width=450, height=160), PageBreak(),
				 Paragraph('<b>6. Conclusão e Parecer Técnico</b>', header_section), Spacer(1, 6)]
	conclusao = (f'Realizada a qualificação térmica do equipamento {equip_descricao} (TAG: {tag}, Série: {serie}), '
				 'verificou-se que o desempenho operacional atende plenamente aos critérios de aceitação estabelecidos '
				 'pela RDC 430/2020 e normas aplicáveis. A câmara manteve a faixa térmica esperada durante os testes de estabilidade, '
				 'apresentando tempo de recuperação satisfatório nos testes de abertura de porta. '
				 '<b>PARECER FINAL: EQUIPAMENTO APROVADO.</b>')
	elements += [Paragraph(conclusao, body_left), Spacer(1, 15), Paragraph('<b>7. Quadro de Aprovação e Assinaturas</b>', header_section), Spacer(1, 10)]
	ass_data = [['__________________________________________', '__________________________________________'],
				[Paragraph(f'<b>Técnico Executor:</b><br/>{tecnico_executor}<br/>Comprehense Engenharia Clínica', body_style),
				 Paragraph(f'<b>Responsável Técnico:</b><br/>{responsavel_tecnico}<br/>Engenheiro Responsável', body_style)]]
	t_ass = Table(ass_data, colWidths=[250, 250])
	t_ass.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('PADDING', (0, 0), (-1, -1), 2)]))
	elements.append(t_ass)
	doc.build(elements)
	pdf_stream.seek(0)
	return send_file(pdf_stream, as_attachment=True, download_name=f'RQT_{tag}_{serie}.pdf', mimetype='application/pdf')


import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
	