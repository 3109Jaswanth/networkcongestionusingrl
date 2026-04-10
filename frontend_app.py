import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


RESULTS_DIR = Path('results')


@st.cache_data
def list_json_files(directory: Path, pattern: str):
    if not directory.exists():
        return []
    return sorted([str(p) for p in directory.glob(pattern)])


@st.cache_data
def load_json(path: str):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f'Invalid JSON in {path}: {exc.msg} at line {exc.lineno}, column {exc.colno}'
        ) from exc
    except Exception as exc:
        raise ValueError(f'Unable to read JSON file {path}: {exc}') from exc


def get_algorithm_keys(results):
    return [k for k in results.keys() if k in ['rr', 'wrr', 'hac_bpnn', 'madqn']]


def normalize_summary(results):
    summary = {}
    for alg in get_algorithm_keys(results):
        data = results.get(alg, {})
        summary[alg] = {
            'throughput': float(data.get('throughput', 0) or 0),
            'retransmits': float(data.get('retransmits', data.get('retransmit_rate', 0)) or 0),
            'rtt': float(data.get('rtt', data.get('avg_rtt', 0)) or 0)
        }
    return summary


def create_time_series_df(results, algorithm):
    series = results.get(algorithm, {}).get('time_series', [])
    if not series:
        return pd.DataFrame()
    df = pd.DataFrame(series)
    if 'retransmit_rate' in df.columns:
        df = df.rename(columns={'retransmit_rate': 'retransmits'})
    if 'avg_rtt' in df.columns:
        df = df.rename(columns={'avg_rtt': 'rtt'})
    return df


def build_network_topology(num_switches=4, queue_lengths=None, actions=None):
    angles = np.linspace(0, 2 * np.pi, num_switches, endpoint=False)
    radius = 3
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    nodes = pd.DataFrame({'switch': list(range(num_switches)), 'x': x, 'y': y})

    fig = go.Figure()
    # draw links
    for i in range(num_switches):
        for j in range(i + 1, num_switches):
            weight = 1.5
            color = 'lightgray'
            fig.add_trace(go.Scatter(
                x=[x[i], x[j]], y=[y[i], y[j]],
                mode='lines', line=dict(color=color, width=weight), hoverinfo='none', showlegend=False
            ))

    # draw actions
    if actions is not None and len(actions) == num_switches:
        for switch, path in enumerate(actions):
            target = (switch + 1 + path) % num_switches
            fig.add_trace(go.Scatter(
                x=[x[switch], x[target]], y=[y[switch], y[target]],
                mode='lines', line=dict(color='#FF6B6B', width=3),
                hoverinfo='text', text=[f'Switch {switch} → Path {path}'], showlegend=False
            ))

    # draw nodes with queue load
    node_colors = []
    hover_text = []
    for switch in range(num_switches):
        load = 0
        if queue_lengths is not None:
            path_keys = [f"{switch}_{p}" for p in range(int(len(queue_lengths) / num_switches))]
            load = np.mean([queue_lengths.get(k, 0) for k in path_keys])
        node_colors.append(load)
        hover_text.append(f"Switch {switch}<br>Avg queue={load:.1f}")

    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        marker=dict(size=24, color=node_colors, colorscale='YlOrRd', showscale=True, colorbar=dict(title='Queue')),
        text=[f'S{idx}' for idx in nodes.switch], textposition='middle center', hovertext=hover_text,
        hoverinfo='text', showlegend=False
    ))

    fig.update_layout(
        title='Network Topology & Path Decisions',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white', margin=dict(l=20, r=20, t=50, b=20), height=500
    )
    fig.update_yaxes(scaleanchor='x', scaleratio=1)
    return fig


def render_overview(summary):
    df = pd.DataFrame(summary).T
    df['score'] = df['throughput'] - df['retransmits'] - df['rtt'] / 10
    df = df.sort_values('score', ascending=False)
    st.metric('Best Algorithm', df.index[0].upper())
    st.write(df[['throughput', 'retransmits', 'rtt']].style.format({
        'throughput': '{:.2f}%', 'retransmits': '{:.2f}%', 'rtt': '{:.2f} ms'}))


def render_comparison_chart(summary):
    df = pd.DataFrame(summary).T.reset_index().rename(columns={'index': 'algorithm'})
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Throughput', x=df.algorithm, y=df.throughput, marker_color='#4ECDC4'))
    fig.add_trace(go.Bar(name='Retransmit', x=df.algorithm, y=df.retransmits, marker_color='#FF6B6B'))
    fig.add_trace(go.Bar(name='RTT', x=df.algorithm, y=df.rtt, marker_color='#556270'))
    fig.update_layout(barmode='group', title='Algorithm Performance Comparison', xaxis_title='Algorithm', yaxis_title='Value')
    st.plotly_chart(fig, use_container_width=True)


def render_training_analysis(history):
    df = pd.DataFrame(history)
    st.subheader('Training Progress')
    if 'episode_rewards' in history:
        reward_df = pd.DataFrame({'episode': range(len(history['episode_rewards'])), 'reward': history['episode_rewards']})
        fig = px.line(reward_df, x='episode', y='reward', title='Episode Reward', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    if 'episode_metrics' in history:
        metrics_df = pd.DataFrame(history['episode_metrics'])
        if 'throughput' in metrics_df.columns:
            fig2 = px.line(metrics_df, y=['throughput', 'retransmit_rate', 'avg_rtt'] if 'retransmit_rate' in metrics_df.columns else ['throughput'],
                           labels={'value': 'Metric', 'index': 'Episode'}, title='Episode Metrics')
            st.plotly_chart(fig2, use_container_width=True)
    
    if 'training_losses' in history:
        loss_df = pd.DataFrame({'episode': range(len(history['training_losses'])), 'loss': history['training_losses']})
        fig3 = px.line(loss_df, x='episode', y='loss', title='Training Loss', markers=True)
        st.plotly_chart(fig3, use_container_width=True)


def render_environment_animation(results, algorithm):
    st.subheader(f'Environment Animation: {algorithm.upper()}')
    df = create_time_series_df(results, algorithm)
    if df.empty:
        st.warning('No step-by-step time series available for this simulation file.')
        return

    step = st.slider('Simulation step', 0, int(df.step.max()), 0)
    current = df[df.step == step].iloc[0]
    queue_lengths = current.get('queue_lengths', {}) or {}
    actions = current.get('actions', []) or []

    col1, col2 = st.columns(2)
    with col1:
        st.metric('Throughput', f"{current.throughput:.2f}%")
        st.metric('Retransmit', f"{current.retransmits:.2f}%")
        st.metric('Avg RTT', f"{current.rtt:.2f} ms")

    with col2:
        if actions:
            st.write('Selected actions per switch:')
            st.write({f'S{idx}': f'Path {path}' for idx, path in enumerate(actions)})

    fig = build_network_topology(num_switches=4, queue_lengths=queue_lengths, actions=actions)
    st.plotly_chart(fig, use_container_width=True)

    if queue_lengths:
        q_df = pd.DataFrame([queue_lengths]).T.reset_index()
        q_df.columns = ['path', 'queue_length']
        q_df['switch'] = q_df['path'].apply(lambda x: x.split('_')[0])
        fig2 = px.bar(q_df, x='path', y='queue_length', color='switch', title='Queue Lengths by Path')
        st.plotly_chart(fig2, use_container_width=True)


def main():
    st.set_page_config(page_title='MADQN SDN Dashboard', layout='wide')
    st.title('MADQN 5G SDN Frontend Dashboard')
    st.markdown('Interactive analytics and environment animation for SDN load balancing.')

    if not RESULTS_DIR.exists():
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    sim_files = list_json_files(RESULTS_DIR, 'simulation_results*.json')
    history_files = list_json_files(RESULTS_DIR, 'training_history*.json')
    st.sidebar.header('Data Selection')

    if sim_files:
        sim_file = st.sidebar.selectbox('Choose simulation result', sim_files)
    else:
        sim_file = None
        st.sidebar.warning('No simulation result files found in results/')

    if history_files:
        history_file = st.sidebar.selectbox('Choose training history', history_files)
    else:
        history_file = None
        st.sidebar.warning('No training history files found in results/')

    if sim_file:
        try:
            results = load_json(sim_file)
        except ValueError as error:
            st.error(str(error))
            st.warning('This simulation file appears to be malformed. Try rerunning the simulation and saving a fresh JSON file.')
            results = None

        if results is not None:
            summary = normalize_summary(results)

            st.sidebar.header('Simulation Overview')
            st.sidebar.write(f'File: {os.path.basename(sim_file)}')
            st.sidebar.write(f'Algorithms: {", ".join(get_algorithm_keys(results))}')

            st.header('Simulation Summary')
            render_overview(summary)
            render_comparison_chart(summary)

            algorithm_options = get_algorithm_keys(results)
            if algorithm_options:
                default_index = algorithm_options.index('madqn') if 'madqn' in algorithm_options else 0
                algorithm = st.selectbox('Animate algorithm', algorithm_options, index=default_index)
                render_environment_animation(results, algorithm)
            else:
                st.warning('No algorithm results found in this simulation file.')

    if history_file:
        try:
            history = load_json(history_file)
        except ValueError as error:
            st.error(str(error))
            st.warning('This training history file appears to be malformed. Try rerunning training and saving a fresh JSON file.')
            history = None

        if history is not None:
            st.header('Training Analysis')
            render_training_analysis(history)

    st.sidebar.markdown('---')
    st.sidebar.markdown('**Run this app:**')
    st.sidebar.code('streamlit run frontend_app.py')


if __name__ == '__main__':
    main()
