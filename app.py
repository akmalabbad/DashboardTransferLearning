from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Perbandingan Model | Beban Listrik Panama', page_icon='⚡', layout='wide')
BASE = Path(__file__).resolve().parent / 'Hasil_csv'

@st.cache_data
def load(name):
    return pd.read_csv(BASE / name)

try:
    scores = load('13_akurasi_origin1.csv')
    forecasts = load('12_ramalan_semua_model.csv')
    periods = load('08_periode_uji.csv')
    cv = load('19_akurasi_cv_per_origin.csv')
    cv_summary = load('20_ringkasan_cv.csv')
    hourly = load('16_galat_per_jam.csv')
    intervals = load('17_selang_prediksi.csv')
    dm = load('18_uji_diebold_mariano.csv')
except (FileNotFoundError, pd.errors.ParserError) as exc:
    st.error(f'CSV hasil tidak dapat dibaca: {exc}. Pastikan folder Hasil_csv berada di samping app.py.')
    st.stop()

st.markdown('''<style>
.stApp {background: #f5f8fc; color: #14243b;}
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px;}
[data-testid="stMetric"] {background: white; border: 1px solid #e5edf5; border-radius: 15px; padding: 17px; box-shadow: 0 4px 18px rgba(25,49,80,.04);}
[data-testid="stMetricLabel"] {color: #52677f;}
h1, h2, h3 {color: #122743;}
.hero {background: linear-gradient(110deg,#102b4b,#125c78); border-radius: 20px; padding: 26px 30px; color: white; margin-bottom: 20px;}
.hero h1 {color: white; margin: 0; font-size: 2rem;}
.hero p {color: #d0e4ed; margin: 8px 0 0;}
.small-label {font-size: .75rem; letter-spacing: .15em; font-weight: 700; color: #81d9da;}
</style>''', unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="small-label">PANAMA · LOAD FORECASTING</div><h1>Perbandingan model peramalan</h1><p>Jelajahi akurasi, ramalan, ketidakpastian, dan konsistensi model beban listrik.</p></div>''', unsafe_allow_html=True)

palette = {'Patokan':'#8294a9','Statistik':'#20a3a1','Machine learning':'#4d83d1','Deep learning':'#8e6ac8','Model fondasi':'#ee9a45','Ensemble':'#e66c70'}
with st.sidebar:
    st.markdown('### ⚡ Filter model')
    groups = st.multiselect('Kelompok model', sorted(scores['Kelompok'].dropna().unique()), default=sorted(scores['Kelompok'].dropna().unique()))
    exog = st.selectbox('Variabel eksogen', ['Semua', 'Dengan eksogen', 'Tanpa eksogen'])
    st.caption('Filter berlaku untuk seluruh halaman. Hasil berasal dari CSV yang disimpan oleh notebook; tidak ada pelatihan ulang.')
filtered = scores[scores['Kelompok'].isin(groups)].copy()
if exog != 'Semua':
    filtered = filtered[filtered['Eksogen'] == (exog == 'Dengan eksogen')]
if filtered.empty:
    st.warning('Tidak ada model yang cocok dengan filter. Ubah pilihan di panel samping.')
    st.stop()
models = filtered['Model'].tolist()
winner = filtered.loc[filtered['MASE'].idxmin()]
cv_filtered = cv_summary[cv_summary['Model'].isin(models)]
cv_best = cv_filtered.loc[cv_filtered['MASE rata-rata'].idxmin()]
c1,c2,c3,c4 = st.columns(4)
c1.metric('Model · evaluasi utama', winner['Model'], f"MASE {winner['MASE']:.3f}", delta_color='off')
c2.metric('MAPE · evaluasi utama', f"{winner['MAPE']:.2f}%", 'Lebih rendah lebih baik', delta_color='off')
c3.metric('Model · rata-rata CV', cv_best['Model'], f"MASE {cv_best['MASE rata-rata']:.3f}", delta_color='off')
c4.metric('Model ditampilkan', str(len(models)), f"{len(periods)} origin evaluasi", delta_color='off')
st.caption('Kartu terbaik mengikuti filter model. Evaluasi utama menggunakan origin 1; validasi silang merangkum seluruh origin yang tersedia.')

ranking_tab, forecast_tab, cv_tab, uncertainty_tab = st.tabs(['📊  Peringkat & galat', '📈  Ramalan', '🔁  Validasi silang', '🎯  Ketidakpastian & uji'])
with ranking_tab:
    st.subheader('Peringkat evaluasi utama')
    st.caption('Origin 1 · Nilai yang lebih rendah menunjukkan galat yang lebih kecil.')
    metric = st.selectbox('Metrik peringkat', ['MASE','MAPE','MAE','RMSE'], format_func=lambda x: {'MASE':'MASE · galat relatif terhadap patokan','MAPE':'MAPE · galat persentase (%)','MAE':'MAE · galat absolut (MWh)','RMSE':'RMSE · galat kuadrat (MWh)'}[x])
    ordered = filtered.sort_values(metric, ascending=True)
    fig = px.bar(ordered, x=metric, y='Model', color='Kelompok', orientation='h', color_discrete_map=palette, text_auto='.3f', hover_data=['MAE','RMSE','MAPE','MASE'])
    fig.update_layout(yaxis={'categoryorder':'total descending'}, height=max(360, len(ordered)*37), margin=dict(l=0,r=20,t=10,b=10), legend_title_text='Kelompok', plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, width='stretch')
    with st.expander('Lihat tabel perbandingan dan unduh CSV'):
        table = ordered[['Model','Kelompok','Eksogen','MAE','RMSE','MAPE','MASE','Waktu (detik)']]
        st.dataframe(table, hide_index=True, width='stretch')
        st.download_button('Unduh hasil yang ditampilkan', table.to_csv(index=False).encode('utf-8-sig'), 'peringkat_model.csv', 'text/csv')
    st.subheader('Pola galat menurut jam')
    st.caption('Rata-rata galat absolut per jam pada evaluasi utama, sebagaimana disimpan di CSV.')
    selected_hour = st.multiselect('Model untuk grafik galat', models, default=ordered['Model'].head(min(4,len(models))).tolist(), key='hours')
    if selected_hour:
        long = hourly.melt(id_vars='Jam', value_vars=selected_hour, var_name='Model', value_name='Galat absolut')
        fig = px.line(long, x='Jam', y='Galat absolut', color='Model', markers=True, labels={'Galat absolut':'Galat absolut (MWh)'})
        fig.update_layout(hovermode='x unified', xaxis=dict(dtick=2), plot_bgcolor='white', legend_title_text='')
        st.plotly_chart(fig, width='stretch')

with forecast_tab:
    st.subheader('Aktual dan ramalan')
    a,b = st.columns([1,2])
    origin = a.selectbox('Origin', sorted(forecasts['origin'].unique()), format_func=lambda x: f'Origin {x}' + (' · evaluasi utama' if x == 1 else ' · validasi silang'))
    chosen = b.multiselect('Bandingkan model', models, default=ordered['Model'].head(min(3,len(models))).tolist(), key='forecast')
    period = periods[periods['Origin'] == origin]
    if not period.empty:
        st.caption(f"Periode uji tersimpan: {period.iloc[0]['Awal uji']} hingga {period.iloc[0]['Akhir uji']} · {period.iloc[0]['Peran']}")
    subset = forecasts[(forecasts['origin'] == origin) & forecasts['model'].isin(chosen)].copy()
    if subset.empty:
        st.info('Pilih setidaknya satu model dengan ramalan yang tersedia.')
    else:
        subset['ds'] = pd.to_datetime(subset['ds'])
        fig = go.Figure()
        actual = subset.drop_duplicates('ds').sort_values('ds')
        fig.add_trace(go.Scatter(x=actual['ds'], y=actual['aktual'], name='Aktual', line=dict(color='#142b49', width=3)))
        for model in chosen:
            part = subset[subset['model'] == model].sort_values('ds')
            if not part.empty:
                fig.add_trace(go.Scatter(x=part['ds'], y=part['mean'], name=model, line=dict(width=2)))
        fig.update_layout(height=480, hovermode='x unified', xaxis_title='Waktu', yaxis_title='Beban (MWh)', legend_title_text='', plot_bgcolor='white')
        st.plotly_chart(fig, width='stretch')
        st.caption('Gunakan zoom dan legenda pada grafik untuk menelusuri periode atau menyembunyikan model.')

with cv_tab:
    st.subheader('Konsistensi lintas origin')
    st.caption('Rata-rata dan simpangan baku MASE dihitung pada origin yang tercantum di CSV ringkasan; semakin rendah MASE, semakin baik.')
    cv_order = cv_filtered.sort_values('MASE rata-rata')
    fig = px.bar(cv_order, x='MASE rata-rata', y='Model', color='Kelompok', error_x='MASE SD', orientation='h', color_discrete_map=palette, hover_data=['Jumlah origin','MAPE rata-rata (%)'])
    fig.update_layout(yaxis={'categoryorder':'total descending'}, height=max(360,len(cv_order)*38), plot_bgcolor='white', legend_title_text='Kelompok')
    st.plotly_chart(fig, width='stretch')
    cv_metric = st.selectbox('Metrik per origin', ['MASE','MAPE','MAE','RMSE'], key='cvmetric')
    cv_models = st.multiselect('Model untuk tiap origin', models, default=cv_order['Model'].head(min(4,len(models))).tolist(), key='cvmodels')
    if cv_models:
        data = cv[cv['Model'].isin(cv_models)]
        fig = px.line(data, x='origin', y=cv_metric, color='Model', markers=True, labels={'origin':'Origin'})
        fig.update_layout(xaxis=dict(dtick=1), hovermode='x unified', plot_bgcolor='white', legend_title_text='')
        st.plotly_chart(fig, width='stretch')
    with st.expander('Tabel ringkasan validasi silang dan periode uji'):
        st.dataframe(cv_order, hide_index=True, width='stretch')
        st.dataframe(periods, hide_index=True, width='stretch')

with uncertainty_tab:
    st.subheader('Cakupan selang prediksi')
    st.caption('Cakupan adalah persentase nilai aktual yang berada di dalam selang prediksi pada origin 1. Garis putus-putus menunjukkan cakupan nominal, 80% atau 95%.')
    cover = st.radio('Tingkat selang', [80,95], horizontal=True)
    column = f'Cakupan {cover}% (%)'
    data = intervals[intervals['Model'].isin(models)].dropna(subset=[column]).sort_values(column)
    if data.empty:
        st.info('Tidak ada cakupan selang yang tersedia untuk model terpilih.')
    else:
        fig = px.bar(data, x=column, y='Model', orientation='h', color=column, color_continuous_scale=['#8ccbd0','#176a82'], range_color=[0,100], hover_data=['Winkler','Selang Winkler'])
        fig.add_vline(x=cover, line_dash='dash', line_color='#e56b57')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_range=[0,105], height=max(330,len(data)*38), plot_bgcolor='white', coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(data, hide_index=True, width='stretch')
    st.subheader('Uji Diebold–Mariano')
    st.caption('Hasil uji yang disimpan notebook; p-value Holm telah dikoreksi untuk pengujian berganda. Pembanding mengikuti filter model; model acuan ditentukan oleh analisis notebook.')
    dm_filtered = dm[dm['Pembanding'].isin(models)]
    if dm_filtered.empty:
        st.info('Tidak ada pembanding uji yang cocok dengan filter.')
    else:
        st.dataframe(dm_filtered, hide_index=True, width='stretch', column_config={'p-value':st.column_config.NumberColumn(format='%.3g'), 'p-value (Holm)':st.column_config.NumberColumn(format='%.3g')})

st.caption('Sumber: Hasil_csv · Perbandingan_Metode_Beban_Listrik_Panama.ipynb')

