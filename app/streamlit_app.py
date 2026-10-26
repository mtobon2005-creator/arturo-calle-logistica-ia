from __future__ import annotations

import random

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Arturo Calle · Logística inteligente", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

# -----------------------------------------------------------------------------
# Base de conocimiento: red, umbrales, hechos iniciales y reglas de Entrega 2.
# Los pesos de las aristas son minutos estimados de viaje en hora pico.
# -----------------------------------------------------------------------------
ORIGEN = "Bodega Itagüí"
ATENCION = 15
RED = {
    ORIGEN: {"Sabaneta Plaza": 8, "Los Molinos Envigado": 12, "C.C. Oviedo": 10},
    "Sabaneta Plaza": {ORIGEN: 8},
    "Los Molinos Envigado": {ORIGEN: 12, "C.C. Premium Plaza": 9},
    "C.C. Oviedo": {ORIGEN: 10, "C.C. El Tesoro": 5, "Unicentro": 9},
    "C.C. El Tesoro": {"C.C. Oviedo": 5, "C.C. Premium Plaza": 7, "C.C. San Diego": 11},
    "C.C. Premium Plaza": {"Los Molinos Envigado": 9, "C.C. El Tesoro": 7},
    "Unicentro": {"C.C. Oviedo": 9, "C.C. San Diego": 8, "C.C. Mayorca": 13},
    "C.C. San Diego": {"C.C. El Tesoro": 11, "Unicentro": 8, "Puerta del Norte": 10},
    "C.C. Mayorca": {"Unicentro": 13, "Puerta del Norte": 7},
    "Puerta del Norte": {"C.C. San Diego": 10, "C.C. Mayorca": 7},
}
HECHOS_INICIALES = {
    "C.C. Oviedo": (15, 60, 5, 1), "C.C. El Tesoro": (45, 30, 18, 0),
    "Unicentro": (18, 40, 9, 4), "C.C. Mayorca": (80, 20, 3, 0),
    "Puerta del Norte": (10, 55, 12, 0), "C.C. San Diego": (60, 25, 7, 0),
    "C.C. Premium Plaza": (22, 15, 20, 0), "Los Molinos Envigado": (90, 10, 2, 0),
    "Sabaneta Plaza": (12, 35, 30, 0),
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#14251f; --muted:#65736d; --green:#176b50; --lime:#d6f27a; --line:#e5ebe7; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
.stApp { background: #f6f8f5; }
.block-container { padding-top:1.5rem; max-width:1440px; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
.hero { border-radius:24px; padding:30px 34px; color:white; background:linear-gradient(115deg,#143c31,#176b50 70%,#318567); margin-bottom:22px; }
.hero .eyebrow { text-transform:uppercase; letter-spacing:.14em; color:#d6f27a; font-size:.72rem; font-weight:700; }
.hero h1 { color:white; margin:.3rem 0; font-size:2.25rem; }
.hero p { color:#dce9e1; max-width:850px; margin:.2rem 0 0; }
.card { background:white; border:1px solid var(--line); padding:18px 20px; border-radius:18px; box-shadow:0 4px 18px #14251f08; }
.small { color:var(--muted); font-size:.88rem; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { border-radius:999px; padding:8px 16px; }
section[data-testid="stSidebar"] { background:#eef3ee; }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:14px 16px; border-radius:16px; }
.stButton>button[kind="primary"] { background:#176b50; border-color:#176b50; border-radius:12px; }
hr { border-color:var(--line); }
</style>
""", unsafe_allow_html=True)


def dijkstra(start: str) -> dict[str, int]:
    dist = {n: 10**9 for n in RED}; dist[start] = 0; pending = set(RED)
    while pending:
        node = min(pending, key=dist.get); pending.remove(node)
        if dist[node] >= 10**9: break
        for neighbor, minutes in RED[node].items():
            if dist[node] + minutes < dist[neighbor]: dist[neighbor] = dist[node] + minutes
    return dist

DIST = {n: dijkstra(n) for n in RED}


def trap(x: float, a: float, b: float, c: float, d: float) -> float:
    if x <= a or x >= d: return 0.0
    if b <= x <= c: return 1.0
    if x < b: return (x-a)/(b-a) if b != a else 1.0
    return (d-x)/(d-c) if d != c else 1.0


def tri(x: float, a: float, b: float, c: float) -> float:
    return max(0.0, min((x-a)/(b-a) if x > a and b != a else (1.0 if x == b else 0.0), (c-x)/(c-b) if x < c and c != b else (1.0 if x == b else 0.0)))


def memberships(f: dict, weekend: bool) -> dict[str, float]:
    inv, sales, days, complaints = f["Inventario"], f["Ventas/semana"], f["Días sin reabastecer"], f["Quejas"]
    high_sales_cut = 40 if weekend else 50
    # Funciones trapezoidales/triangulares: solapamiento suave, con rangos
    # anclados a los umbrales del experto original.
    return {
        "inv_muy_bajo": trap(inv, -100, -100, 5, 15),
        "inv_critico": trap(inv, 5, 10, 18, 26),
        "inv_bajo_30": trap(inv, 15, 20, 27, 35),
        "inv_sobrante": trap(inv, 85, 100, 150, 150),
        "ventas_altas": trap(sales, high_sales_cut-15, high_sales_cut, high_sales_cut+15, high_sales_cut+30),
        "rotacion_muy_alta": trap(sales, 55, 70, 120, 120),
        "dias_medios": trap(days, 8, 14, 22, 29),
        "dias_muy_altos": trap(days, 18, 25, 45, 45),
        "quejas_altas": trap(complaints, 1, 3, 8, 8),
        "fin_semana": 1.0 if weekend else 0.0,
    }


def fuzzy_priority(f: dict, weekend: bool) -> dict:
    m = memberships(f, weekend)
    rules = [
        (m["inv_muy_bajo"], 96, "R1 difusa · inventario muy bajo"),
        (m["quejas_altas"], 94, "R2 difusa · quejas recientes"),
        (m["dias_muy_altos"], 92, "R3 difusa · demora extrema"),
        (min(m["inv_critico"], m["ventas_altas"]), 91, "R4 difusa · inventario crítico + ventas altas"),
        (m["inv_critico"], 62, "R5 difusa · inventario crítico"),
        (m["dias_medios"], 58, "R6 difusa · días sin reabastecer"),
        (m["rotacion_muy_alta"], 55, "R7 difusa · alta rotación"),
        (min(m["fin_semana"], m["inv_bajo_30"]), 52, "R8 difusa · fin de semana + inventario bajo"),
        (m["inv_sobrante"], 12, "R9 difusa · inventario sobrante"),
    ]
    # Consecuentes tipo Sugeno (centroid ponderado de salidas singleton).
    weights = [w for w, _, _ in rules if w > 0]
    score = sum(w*v for w,v,_ in rules) / sum(weights) if weights else 18.0
    fired = sorted([(w, label) for w, _, label in rules if w > .05], reverse=True)
    # Clasificación lingüística legible, conservando el puntaje continuo.
    label = "Urgente" if score >= 75 else "Media" if score >= 38 else "Baja"
    return {"score": score, "priority": label, "rules": [x[1] for x in fired[:3]], "memberships": m}


def discrete_priority(f: dict, weekend: bool) -> dict:
    inv, sales, days, complaints = f["Inventario"], f["Ventas/semana"], f["Días sin reabastecer"], f["Quejas"]
    high_cut = 40 if weekend else 50
    tests = [
        (inv < 10, "Urgente", "R1 · inventario muy bajo"),
        (complaints > 3, "Urgente", "R2 · más de 3 quejas"),
        (days > 25, "Urgente", "R3 · más de 25 días sin reabastecer"),
        (inv < 20 and sales > high_cut, "Urgente", "R4 · inventario crítico + ventas altas"),
        (inv < 20, "Media", "R5 · inventario crítico"),
        (days > 14, "Media", "R6 · más de 14 días sin reabastecer"),
        (sales > 70, "Media", "R7 · rotación muy alta"),
        (weekend and inv < 30, "Media", "R8 · fin de semana + inventario bajo"),
        (inv > 100, "Baja", "R9 · inventario sobrante"),
    ]
    for ok, label, rule in tests:
        if ok: return {"score": {"Urgente": 92, "Media": 56, "Baja": 18}[label], "priority": label, "rules": [rule]}
    return {"score": 18.0, "priority": "Baja", "rules": ["R10 · ninguna condición anterior"]}


def plan_route(stores: list[str], scores: dict, limits: dict, time_budget: int, scenario_expand: bool, focus: bool, seed: int = 42):
    if not stores: return [], [], 0, 0.0, []
    random.seed(seed)
    names = list(stores)
    disputed = {"C.C. Oviedo", "Unicentro", "C.C. El Tesoro", "C.C. San Diego"}
    values = {n: max(.2, scores[n] / 100) * (2 if focus and n in disputed else 1) for n in names}
    def decode(order):
        visited=[]; elapsed=0; current=ORIGEN; arrivals={}; route=[ORIGEN]
        for name in order:
            travel=DIST[current][name]
            if elapsed + travel + ATENCION + DIST[name][ORIGEN] <= time_budget:
                elapsed += travel; arrivals[name]=elapsed; elapsed += ATENCION
                visited.append(name); route.append(name); current=name
        total=elapsed + DIST[current][ORIGEN]
        return visited,total,arrivals,route+[ORIGEN]
    def fitness(order):
        visited,total,arrivals,_=decode(order)
        value=sum(values[n] * (.5 if scenario_expand and n in disputed and arrivals[n] > 45 else 1) for n in visited)
        return value - .01*total
    # Algoritmo genético de Entrega 3: 30 individuos, 60 generaciones,
    # ruleta proporcional, cruce por orden, mutación 20%, élite 2.
    pop=[random.sample(names,len(names)) for _ in range(30)]
    for _ in range(60):
        pop.sort(key=fitness, reverse=True); nxt=pop[:2]
        while len(nxt)<30:
            raw=[fitness(individual) for individual in pop]
            floor=min(raw)
            weights=[max(.001,value-floor+.01) for value in raw]
            p1,p2=random.choices(pop,weights=weights,k=2)
            cut=max(1,len(names)//2)
            child=p1[:cut]+[x for x in p2 if x not in p1[:cut]]
            if len(child)>1 and random.random()<.20:
                a,b=random.sample(range(len(child)),2); child[a],child[b]=child[b],child[a]
            nxt.append(child)
        pop=nxt
    best=max(pop,key=fitness)
    visited,total,arrivals,route=decode(best)
    return route, [n for n in names if n not in visited], total, fitness(best), visited


def allocate_load(frame: pd.DataFrame, scores: dict, coverage_days: int, capacity: int, safety: int):
    rows=[]
    for _,r in frame.iterrows():
        daily=float(r["Ventas/semana"])/7
        target=round(daily*coverage_days+safety)
        need=max(0,target-int(r["Inventario"]))
        rows.append({"Tienda":r["Tienda"],"Necesidad objetivo":need,"Prioridad difusa":scores[r["Tienda"]],"Envío":0})
    # Reparto incremental: cada unidad se asigna a la tienda con mayor
    # prioridad por cobertura de la necesidad objetivo (recalcula en cada ronda).
    remaining=capacity
    while remaining>0:
        candidates=[x for x in rows if x["Envío"]<x["Necesidad objetivo"]]
        if not candidates: break
        chosen=max(candidates,key=lambda x:(x["Prioridad difusa"]*(1-x["Envío"]/max(1,x["Necesidad objetivo"])), -x["Envío"]))
        chosen["Envío"]+=1; remaining-=1
    return pd.DataFrame(rows)

st.sidebar.markdown("### Arturo Calle")
st.sidebar.caption("Sistema de apoyo logístico · Fundamentos de IA")
page = st.sidebar.radio("Navegación", ["Panel del día", "Base de conocimiento", "Estrategia competitiva", "Cómo funciona"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption("Modelo académico con datos simulados de los sprints 1–3. Las rutas y tiempos son estimaciones del proyecto.")

st.markdown('<div class="hero"><div class="eyebrow">Fundamentos de inteligencia artificial · Sprints 1–3</div><h1>Logística más clara. Decisiones más ágiles.</h1><p>Unificamos la red de tiendas, las reglas del experto y la planificación de reparto en un panel operativo sencillo. Explora la prioridad difusa, arma una ruta y distribuye la carga.</p></div>', unsafe_allow_html=True)

if "stores_df" not in st.session_state:
    st.session_state.stores_df = pd.DataFrame([{"Tienda":n,"Inventario":v[0],"Ventas/semana":v[1],"Días sin reabastecer":v[2],"Quejas":v[3]} for n,v in HECHOS_INICIALES.items()])
if page == "Panel del día":
    st.markdown("## Planificar el reparto")
    st.markdown('<p class="small">Actualiza los datos de hoy; el sistema explica sus recomendaciones y permite revisarlas antes de planear.</p>', unsafe_allow_html=True)
    a,b,c=st.columns([1,1,1])
    with a: weekend=st.toggle("Se acerca el fin de semana", value=True)
    with b: time_budget=st.slider("Tiempo máximo de ruta (min)",30,240,90,step=5)
    with c: fuzzy=st.toggle("Prioridad difusa",value=True,help="Activa rangos graduales en lugar de cortes rígidos.")
    st.markdown("### 1 · Estado de las tiendas")
    edited=st.data_editor(st.session_state.stores_df, use_container_width=True, hide_index=True, num_rows="dynamic", column_config={"Tienda":st.column_config.TextColumn(required=True),"Inventario":st.column_config.NumberColumn(min_value=0,max_value=10000,step=1),"Ventas/semana":st.column_config.NumberColumn(min_value=0,max_value=10000,step=1),"Días sin reabastecer":st.column_config.NumberColumn(min_value=0,max_value=365,step=1),"Quejas":st.column_config.NumberColumn(min_value=0,max_value=10000,step=1)})
    st.session_state.stores_df=edited
    if edited.empty or edited["Tienda"].isna().any() or edited["Tienda"].duplicated().any() or edited[["Inventario", "Ventas/semana", "Días sin reabastecer", "Quejas"]].isna().any().any():
        st.warning("Completa todos los campos y usa un nombre único para cada tienda.")
    else:
        results={}
        for _,row in edited.iterrows():
            facts={k:float(row[k]) for k in ["Inventario","Ventas/semana","Días sin reabastecer","Quejas"]}
            results[row["Tienda"]]=(fuzzy_priority(facts,weekend) if fuzzy else discrete_priority(facts,weekend))
        with st.expander("Capa de carga · ¿cuántas unidades enviar?", expanded=True):
            x,y,z=st.columns(3)
            with x: capacity=st.number_input("Capacidad disponible (unidades)",min_value=0,max_value=100000,value=250,step=10)
            with y: cover=st.slider("Cobertura objetivo (días)",1,21,7)
            with z: safety=st.number_input("Stock de seguridad por tienda",min_value=0,max_value=500,value=5,step=1)
            load=allocate_load(edited, {n:int(r["score"]) for n,r in results.items()}, cover,int(capacity),int(safety))
            total=int(load["Envío"].sum())
            m1,m2,m3=st.columns(3); m1.metric("Unidades asignadas",f"{total:,}"); m2.metric("Capacidad sin usar",f"{int(capacity)-total:,}"); m3.metric("Tiendas con carga",int((load["Envío"]>0).sum()))
            st.dataframe(load.sort_values(["Envío","Prioridad difusa"],ascending=False).rename(columns={"Prioridad difusa":"Prioridad (0–100)"}),use_container_width=True,hide_index=True)
            st.caption("La necesidad objetivo se estima con ventas semanales / 7 × días de cobertura + stock de seguridad − inventario actual. La capacidad se reparte primero a mayor prioridad y luego a tiendas con mayor brecha restante.")
        st.markdown("### 2 · Prioridad explicable")
        ptab=pd.DataFrame([{"Tienda":n,"Prioridad":r["priority"],"Puntaje difuso":round(r["score"],1),"Reglas activadas":", ".join(r["rules"])} for n,r in results.items()]).sort_values("Puntaje difuso",ascending=False)
        st.dataframe(ptab,use_container_width=True,hide_index=True,column_config={"Puntaje difuso":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.1f")})
        st.markdown("### 3 · Ruta sugerida")
        s1,s2=st.columns([1,1])
        with s1: rival=st.toggle("El competidor se expande",value=True)
        with s2: concentrate=st.toggle("Concentrar inventario en zonas en disputa",value=True)
        scores={n:r["score"] for n,r in results.items()}
        known=[n for n in scores if n in DIST]
        outside=[n for n in scores if n not in DIST]
        if outside: st.info("Tiendas añadidas sin conexión en la red vial quedan fuera del cálculo de ruta: "+", ".join(outside))
        route,pending,minutes,fitness,visited=plan_route(known,scores,time_budget,rival,concentrate)
        u,v,w=st.columns(3); u.metric("Tiempo estimado",f"{minutes} min"); v.metric("Visitas dentro del límite",len(visited)); w.metric("Tiendas pendientes",len(pending))
        st.markdown(" → ".join(f"**{x}**" for x in route))
        st.caption(f"Fitness del algoritmo genético: {fitness:.2f} · Búsqueda sobre la red de tiempos de viaje y 15 min de atención por parada.")
        if pending: st.write("**Pendientes:** "+" · ".join(pending))
        if visited:
            delivered=load[load["Tienda"].isin(visited)][["Tienda","Envío"]].rename(columns={"Envío":"Unidades en esta ruta"})
            st.markdown("#### Carga para las tiendas visitadas")
            st.dataframe(delivered,use_container_width=True,hide_index=True)
elif page == "Base de conocimiento":
    st.markdown("## La base de conocimiento")
    st.markdown("Es el conocimiento estable del modelo. Se separa de la **memoria de trabajo**, que guarda los datos que cambian cada día, y del **motor de inferencia**, que aplica reglas y produce recomendaciones.")
    k1,k2,k3=st.columns(3)
    with k1: st.markdown('<div class="card"><b>1 · Base de conocimiento</b><p class="small">Red vial, tiempos, umbrales y reglas SI–ENTONCES del experto.</p></div>',unsafe_allow_html=True)
    with k2: st.markdown('<div class="card"><b>2 · Memoria de trabajo</b><p class="small">Inventario, ventas, días sin reabastecer, quejas, tiempo y capacidad de hoy.</p></div>',unsafe_allow_html=True)
    with k3: st.markdown('<div class="card"><b>3 · Motor de inferencia</b><p class="small">Prioridad, unidades objetivo, selección de visitas y orden de ruta.</p></div>',unsafe_allow_html=True)
    st.markdown("### Reglas discretas del experto")
    rules=[("R1","Inventario < 10","Urgente"),("R2","Quejas > 3","Urgente"),("R3","Días sin reabastecer > 25","Urgente"),("R4","Inventario < 20 y ventas altas (>40 antes de fin de semana; >50 en otro caso)","Urgente"),("R5","Inventario < 20","Media"),("R6","Días sin reabastecer > 14","Media"),("R7","Ventas > 70 unidades/semana","Media"),("R8","Fin de semana próximo e inventario < 30","Media"),("R9","Inventario > 100","Baja"),("R10","Ninguna regla anterior aplica","Baja")]
    st.dataframe(pd.DataFrame(rules,columns=["Regla","Condición","Conclusión"]),use_container_width=True,hide_index=True)
    st.markdown("### Capa difusa añadida")
    st.write("Las entradas se representan con funciones triangulares/trapezoidales solapadas (por ejemplo, inventario crítico empieza a perder pertenencia gradualmente alrededor de 20 unidades). Las reglas conservan la base experta, pero su intensidad activa las conclusiones en distinto grado. Un consecuente Sugeno usa salidas singleton (urgente 90+, media 50–62, baja 12–18) y centroide ponderado para obtener un puntaje continuo de 0 a 100. Los cortes de etiqueta son solo una lectura resumida; el orden usa el puntaje continuo.")
    st.markdown("### Red vial del proyecto")
    edges=[]
    for a,links in RED.items():
        for b,mins in links.items():
            if a < b: edges.append({"Tramo":f"{a} ↔ {b}","Tiempo (min)":mins})
    st.dataframe(pd.DataFrame(edges),use_container_width=True,hide_index=True)
    st.caption("Son tiempos académicos simulados de hora pico, tomados de los materiales adjuntos; no son tráfico en tiempo real.")
elif page == "Estrategia competitiva":
    st.markdown("## Decisión frente a la expansión del competidor")
    st.write("La matriz de pagos de la Entrega 3 usa valores hipotéticos de participación de mercado (escala 0–100 en los notebooks; la presentación los describe como escala 0–10). Se muestra la matriz original tal como está codificada, y se explica el supuesto para no confundirlo con datos reales.")
    payoff=pd.DataFrame([[20,50],[65,80]],index=["Concentrar","Distribuir"],columns=["Competidor se expande","Competidor mantiene"])
    st.dataframe(payoff,use_container_width=True)
    st.info("Los pagos son supuestos didácticos. La conclusión de equilibrio depende de esos valores. El escenario de ruta aplica un valor ×2 a tiendas en disputa cuando se concentra inventario, y reduce 50% el valor de una visita posterior al minuto 45 si el rival se expande.")
    st.markdown("**Zonas de disputa consideradas en el modelo:** C.C. Oviedo, Unicentro, C.C. El Tesoro y C.C. San Diego. El algoritmo genético propone el orden de visita que maximiza valor entregado menos una penalización pequeña por tiempo.")
    st.caption("Los adjuntos contienen dos variantes de teoría de juegos; esta app conserva la matriz y el escenario interactivo descritos en la presentación de Entrega 3 y deja claros sus supuestos.")
else:
    st.markdown("## De los sprints a una sola herramienta")
    steps=[("Sprint 1 · Búsqueda A*","Modeló la red de nueve tiendas con aristas en minutos. Dijkstra obtiene los caminos más cortos entre puntos; A* estimó una vuelta cerrada de 104 min para atender todas las tiendas."),("Sprint 2 · Sistema experto","Separa base de conocimiento, memoria de trabajo e inferencia. Diez reglas priorizan tiendas; la ruta respeta el tiempo disponible y los 15 min de atención."),("Sprint 3 · Juego y algoritmo genético","Evalúa escenarios competitivos y busca un orden de visita con mejor valor dentro de la jornada. En esta app se ejecuta sobre la misma red local del proyecto."),("Extensión · Lógica difusa y carga","Suaviza los umbrales para comparar prioridades cercanas y decide cuánto enviar a cada tienda con capacidad limitada." )]
    for title,body in steps:
        with st.container(border=True): st.markdown(f"### {title}"); st.write(body)
    st.warning("El modelo es un prototipo académico: no consulta inventario real, tráfico en vivo ni geolocalización, y sus supuestos deben validarse con el equipo logístico antes de uso operativo.")
    st.markdown("### Fuente")
    st.write("Implementación basada en los notebooks Entrega 2 y Entrega 3 y los tres HTML compartidos: panel interactivo, presentación del sprint y sistema experto de 10 reglas.")

st.markdown("---")
st.caption("Proyecto de Fundamentos de IA · Arturo Calle · Mariana Tobón y María Clara Escobar · Sprints 1–3")



