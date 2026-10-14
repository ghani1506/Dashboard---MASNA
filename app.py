import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from analytics import GRADES,DEFAULT_BOUNDS,parse_workbook,flatten

st.set_page_config(page_title='MASNA Examination Analytics',page_icon='📊',layout='wide')
st.markdown('''<style>.stApp{background:#f4f7f7}h1,h2,h3{color:#163b3d}div[data-testid="stMetric"]{background:white;border:1px solid #e1e9e7;border-radius:12px;padding:20px}section[data-testid="stSidebar"]{background:#e8f1ee}.block-container{padding-top:2rem}button{border-radius:7px!important}</style>''',unsafe_allow_html=True)
if 'books' not in st.session_state: st.session_state.books=[]
if 'rules' not in st.session_state: st.session_state.rules=dict(bounds=DEFAULT_BOUNDS.copy(),credit=59.5,component='score',excluded=['PHYSICAL EDUCATION','MELAYU ISLAM BERAJA'],confirmed=False)
rules=st.session_state.rules
with st.sidebar:
 st.title('MASNA')
 st.caption('EXAMINATION SECTION · SMPAPHMASNA')
 page=st.radio('Workspace',['Overview','Master mark sheet','Subject analysis','Credit analysis','Data review','Calculation rules'])
 st.divider()
 uploads=st.file_uploader('Import mark sheets or dashboard backup',type=['xlsx','json'],accept_multiple_files=True)
 if st.button('Load selected files',type='primary'):
  for f in uploads or []:
   try:
    if f.name.lower().endswith('.json'):
     x=json.loads(f.getvalue()); bs=x['books'] if isinstance(x,dict) else x
     if not isinstance(bs,list) or not all(isinstance(b,dict) and isinstance(b.get('records'),list) for b in bs): raise ValueError('Invalid dashboard backup')
     if isinstance(x,dict) and 'rules' in x: st.session_state.rules=x['rules']
    else: bs=[parse_workbook(f.getvalue(),f.name)]
    for b in bs:
     st.session_state.books=[old for old in st.session_state.books if old['file']!=b['file']]+[b]
   except Exception as e: st.error(f'{f.name}: {e}')
  st.rerun()
 st.download_button('Download session backup',json.dumps(dict(books=st.session_state.books,rules=st.session_state.rules),ensure_ascii=False),'MASNA-backup.json','application/json')
 if st.button('Clear session data'):
  st.session_state.books=[];st.rerun()
 st.caption('Uploads are held in this session. Download a backup before closing. No student data is bundled in the GitHub source.')
st.caption('SMPAPHMASNA / EXAMINATION SECTION')
st.title('Examination '+page.lower() if page=='Overview' else page)
books=st.session_state.books
if not books:
 st.info('Upload your Excel master mark sheets, or import a JSON backup from the existing dashboard, then click Load selected files.')
 st.stop()
if page=='Calculation rules':
 subjects=sorted({m['subject'] for b in books for r in b['records'] for m in r['marks']})
 with st.form('rules'):
  component=st.selectbox('Assessment component',['score','task','continuous'],index=['score','task','continuous'].index(rules['component']),format_func=lambda x:dict(score='Examination marks',task='Assessment task',continuous='Continuous assessment')[x])
  columns=st.columns(3); bounds=[]
  for i,g in enumerate(GRADES):
   with columns[i%3]: bounds.append(st.number_input(g+' lower boundary',0.0,100.0,float(rules['bounds'][i]),0.1))
  credit=st.number_input('Credit threshold',0.0,100.0,float(rules['credit']),0.1)
  eligible=st.multiselect('Subjects eligible for student totals, averages and credits',subjects,default=[s for s in subjects if s not in rules['excluded']])
  st.caption('Unrounded marks. Competition ranking (1, 2, 2, 4) within class, examination and matching eligible subject sets. No whole-school rank.')
  if st.form_submit_button('Apply reviewed rules'):
   if bounds[-1]!=0 or any(a<=b for a,b in zip(bounds,bounds[1:])): st.error('Boundaries must strictly descend, with U starting at 0.')
   else:
    st.session_state.rules=dict(bounds=bounds,credit=credit,component=component,excluded=[s for s in subjects if s not in eligible],confirmed=True);st.rerun()
 st.stop()
if not rules.get('confirmed'): st.warning('Provisional rules: credit ≥59.5; PE and MIB excluded from totals. Review Calculation rules before official reporting.')
df=pd.DataFrame(flatten(books,rules['component'],rules['bounds'],rules['excluded']))
cols=st.columns(4)
for c,key in zip(cols,['Year','Examination','Class','Subject']):
 with c:
  choice=st.selectbox(key,['All']+sorted(df[key].unique().tolist()))
  if choice!='All': df=df[df[key]==choice]
if df.empty: st.info('No matching records');st.stop()
st.caption(f"{df['ID'].nunique()} student examination records · {df['Source'].nunique()} workbooks · {rules['component']} marks")
safe=df.copy()
for c in safe.select_dtypes(include='object'):
 safe[c]=safe[c].map(lambda x:"'"+x if isinstance(x,str) and x.startswith(('=','+','-','@')) else x)
st.download_button('Export filtered results CSV',safe.to_csv(index=False).encode('utf-8-sig'),'MASNA-results.csv','text/csv')
assessed=df.dropna(subset=['Mark'])
def rate(n,d): return f'{100*n/d:.1f}%' if d else '—'
summary=assessed.groupby('Subject')['Mark'].agg(Assessed='count',Mean='mean',Median='median').reset_index()
for name,bound in [('A*–C6',rules['bounds'][5]),('A*–E8',rules['bounds'][7])]:
 counts=assessed.assign(Pass=assessed.Mark>=bound).groupby('Subject').Pass.sum()
 summary[name+' count']=summary.Subject.map(counts)
 summary[name+' %']=100*summary[name+' count']/summary.Assessed
palette=['#146c63','#478e81','#7aad9c','#a3c5b6','#c3d6bf','#d6debf','#c7a165','#c68c59','#b56e52']
def dist_chart():
 counts=assessed.Grade.value_counts().reindex(GRADES,fill_value=0)
 fig=px.bar(x=counts.index,y=counts.values,color=counts.index,color_discrete_sequence=palette,labels={'x':'Grade','y':'Subject entries'})
 fig.update_layout(showlegend=False,plot_bgcolor='white',paper_bgcolor='white');st.plotly_chart(fig,use_container_width=True)
if page=='Overview':
 for c,label,value in zip(st.columns(4),['Student exam records','Assessed entries','A*–C6','A*–E8'],[df.ID.nunique(),len(assessed),rate((assessed.Mark>=rules['bounds'][5]).sum(),len(assessed)),rate((assessed.Mark>=rules['bounds'][7]).sum(),len(assessed))]): c.metric(label,value)
 a,b=st.columns([3,2])
 with a:
  st.subheader('Subject achievement');st.plotly_chart(px.bar(summary.sort_values('Mean'),x='Mean',y='Subject',orientation='h',range_x=[0,100],color_discrete_sequence=['#146c63']),use_container_width=True)
 with b: st.subheader('Grade distribution');dist_chart()
 st.subheader('Class performance');st.caption('Subject mixes may differ. These averages are not a class ranking.')
 st.dataframe(assessed.groupby(['Class','Examination']).agg(Assessed_entries=('Mark','count'),Mean_mark=('Mark','mean')).reset_index(),hide_index=True,use_container_width=True)
elif page=='Subject analysis':
 dist_chart();st.dataframe(summary,hide_index=True,use_container_width=True)
 frequencies=pd.crosstab(assessed.Subject,assessed.Grade).reindex(columns=GRADES,fill_value=0)
 st.subheader('Grade frequencies');st.dataframe(frequencies,use_container_width=True)
elif page in ['Master mark sheet','Credit analysis']:
 # Use all subjects for selected students; a subject filter must not redefine totals.
 full=pd.DataFrame(flatten(books,rules['component'],rules['bounds'],rules['excluded']))
 full=full[full.ID.isin(df.ID.unique())];eligible=full[full.Eligible]
 student=full[['ID','Student','Class','Examination']].drop_duplicates('ID').set_index('ID')
 g=eligible.groupby('ID').Mark
 student['Assessed']=g.count();student['Expected']=g.size();student['Total']=g.sum(min_count=1);student['Average']=g.mean()
 student['Credits']=eligible.assign(Credit=eligible.Mark>=rules['credit']).groupby('ID').Credit.sum()
 student['Complete']=student.Assessed.eq(student.Expected)&student.Assessed.gt(0)
 signatures=eligible.groupby('ID').Subject.apply(lambda s:'|'.join(sorted(s)))
 student['Subject set']=signatures;student['Position']=None
 mask=student.Complete
 student.loc[mask,'Position']=student[mask].groupby(['Class','Examination','Subject set']).Total.rank(method='min',ascending=False)
 if page=='Credit analysis':
  st.caption(f"Credit threshold ≥{rules['credit']}. Compare matching pathways and examinations.")
  st.plotly_chart(px.histogram(student,x='Credits',color_discrete_sequence=['#146c63']),use_container_width=True)
  st.dataframe(student.reset_index().drop(columns=['Subject set']),hide_index=True,use_container_width=True)
 else:
  search=st.text_input('Search student or class');view=student[student.Student.str.contains(search,case=False,regex=False)|student.Class.str.contains(search,case=False,regex=False)]
  marks=df.pivot_table(index='ID',columns='Subject',values='Mark',aggfunc='first',dropna=False)
  st.dataframe(view.join(marks).drop(columns=['Subject set']),use_container_width=True)
  st.caption('Incomplete totals are partial. Blank marks are not zero. Positions only include complete records with matching eligible subjects.')
  pick=st.selectbox('Student details',view.index.tolist(),format_func=lambda x:view.loc[x,'Student']+' · '+view.loc[x,'Class'])
  if pick: st.dataframe(full[full.ID==pick][['Subject','Mark','Grade','Eligible','Status','Source cell']],hide_index=True,use_container_width=True)
elif page=='Data review':
 st.info('Saved Master-sheet errors include unused template cells. Blank entries may represent optional subjects. Confirm enrolment and absence status before reporting completeness. Excel formulas are not recalculated by this app.')
 selected=books if df.empty else [b for b in books if b['file'] in df.Source.unique()]
 st.dataframe(pd.DataFrame([dict(Workbook=b['file'],Class=b['class'],**b['errors']) for b in selected]).fillna(0),hide_index=True,use_container_width=True)
 st.subheader('Blank and non-numeric entries');st.dataframe(df[df.Mark.isna()][['Student','Class','Subject','Status','Source','Source cell']],hide_index=True,use_container_width=True)
st.caption('Uploaded marks remain unchanged. Dashboard calculations follow the selected rules. OneDrive live sync is not configured.')
