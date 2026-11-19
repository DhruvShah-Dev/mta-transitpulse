"""Create and execute the Phase 4 notebook from the exported scorecard."""

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "notebooks" / "03_priority_analysis.ipynb"


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(
            "# 2025 operational priority analysis\n\n"
            "A screening tool for further investigation, not a causal or official MTA allocation model. "
            "The scorecard is generated from `sql/analysis/07_priority_components.sql` by "
            "`src/build_priority_scorecard.py`. See `reports/PRIORITIZATION_METHOD.md`."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import json\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n"
            "ROOT = Path.cwd()\n"
            "data = pd.read_csv(ROOT / 'data/analysis/line_priority_2025.csv')\n"
            "meta = json.loads((ROOT / 'data/analysis/priority_metadata.json').read_text())\n"
            "focus = ['F', 'Q', 'B', 'D']\n"
            "display(data[['line_id','cjt_percent','net_additional_passenger_minutes',"
            "'service_delivered_percent','score_baseline','rank_baseline','priority_quadrant']].head(10).round(2))"
        ),
        nbf.v4.new_markdown_cell(
            "## Priority matrix\n\nVertical and horizontal dividers are the 2025 medians across 23 comparison "
            "groups. Bubble area represents estimated passenger trips. The dividers are descriptive, not targets."
        ),
        nbf.v4.new_code_cell(
            "fig, ax = plt.subplots(figsize=(10, 7))\n"
            "colors = {'High burden / Poor reliability':'#c2410c',"
            "'High burden / Better reliability':'#2563eb',"
            "'Lower burden / Poor reliability':'#d97706',"
            "'Lower burden / Better reliability':'#64748b'}\n"
            "for label, group in data.groupby('priority_quadrant'):\n"
            "    ax.scatter(group.cjt_percent, group.net_additional_passenger_minutes / 1e6, "
            "s=group.passenger_trips / 3e5 + 30, alpha=.65, color=colors[label], label=label, edgecolors='white')\n"
            "ax.axvline(meta['quadrant_cutoffs']['cjt_percent_median'], color='#334155', ls='--', lw=1)\n"
            "ax.axhline(meta['quadrant_cutoffs']['net_additional_passenger_minutes_median']/1e6, "
            "color='#334155', ls='--', lw=1)\n"
            "for row in data.itertuples():\n"
            "    if row.line_id in focus:\n"
            "        ax.annotate(row.line_id, (row.cjt_percent, row.net_additional_passenger_minutes/1e6), "
            "xytext=(5, 6), textcoords='offset points', fontsize=12, weight='bold')\n"
            "ax.set(xlabel='Customer Journey Time Performance (%) → better', "
            "ylabel='Net additional passenger minutes (millions)', "
            "title='2025 customer reliability and passenger-time burden')\n"
            "ax.legend(loc='upper right', fontsize=8)\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell(
            "## F, Q, B, D: underlying measures and history\n\nCJTP is passenger weighted. "
            "AJT uses summed minutes divided by summed trips. Delay and major-incident sources are separate "
            "diagnostics and are not added."
        ),
        nbf.v4.new_code_cell(
            "cols = ['line_id','passenger_trips','cjt_2022_percent','cjt_2023_percent',"
            "'cjt_2024_percent','cjt_percent','cjt_yoy_change_pp','ajt_minutes_per_trip',"
            "'net_additional_passenger_minutes','weekday_delay_incidents',"
            "'weekday_major_incidents','service_delivered_percent','priority_quadrant']\n"
            "display(data.set_index('line_id').loc[focus].reset_index()[cols].round(2))\n"
            "fig, ax = plt.subplots(figsize=(8, 4))\n"
            "for line in focus:\n"
            "    row = data.set_index('line_id').loc[line]\n"
            "    ax.plot([2022,2023,2024,2025], "
            "[row.cjt_2022_percent,row.cjt_2023_percent,row.cjt_2024_percent,row.cjt_percent], "
            "marker='o', label=line)\n"
            "ax.set(xlabel='Year', ylabel='Passenger-weighted CJTP (%)', "
            "title='Customer reliability on the four highlighted services')\n"
            "ax.set_xticks([2022,2023,2024,2025])\n"
            "ax.legend()\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell(
            "## Weight sensitivity and unweighted Pareto frontier\n\n"
            "The five scenarios change analytical weights only. Pareto status uses CJTP and net minutes "
            "without weights. A line is dominated when another line has at least as poor CJTP and "
            "at least as high burden, with one strict difference."
        ),
        nbf.v4.new_code_cell(
            "rank_cols = ['rank_baseline','rank_equal','rank_reliability_focused',"
            "'rank_burden_focused','rank_service_focused']\n"
            "display(data[['line_id',*rank_cols,'rank_best_case','rank_worst_case',"
            "'pareto_customer_frontier']].head(12))\n"
            "fig, ax = plt.subplots(figsize=(10, 5))\n"
            "for line in focus:\n"
            "    row = data.set_index('line_id').loc[line]\n"
            "    ax.plot(range(len(rank_cols)), [row[c] for c in rank_cols], marker='o', label=line)\n"
            "ax.set_xticks(range(len(rank_cols)), ['Baseline','Equal','Reliability','Burden','Service'])\n"
            "ax.set(ylabel='Rank (1 = highest priority)', title='Rank sensitivity for highlighted lines')\n"
            "ax.invert_yaxis()\n"
            "ax.legend()\n"
            "fig.tight_layout()\n"
            "plt.show()\n"
            "display(data.loc[data.pareto_customer_frontier, "
            "['line_id','cjt_percent','net_additional_passenger_minutes']].round(2))"
        ),
    ]
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    client = NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    TARGET.parent.mkdir(exist_ok=True)
    nbf.write(nb, TARGET)
    print(f"{TARGET.relative_to(ROOT)}: {sum(c.cell_type == 'code' for c in nb.cells)} executed code cells")


if __name__ == "__main__":
    main()
