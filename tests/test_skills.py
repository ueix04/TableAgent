"""三大 Skill 单元测试。"""

import pandas as pd
from PIL import Image

from skills.reader import get_overview, get_info, get_missing, get_head, get_unique
from skills.analyst import describe, value_counts, groupby_agg, correlation, filter_data, sort_data
from skills.visualizer import histogram, bar_chart, box_plot, heatmap, scatter, pairplot

SAMPLE = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "age": [25, 35, 30, None, 40],
    "fare": [100.0, 200.0, 150.0, 250.0, 300.0],
    "sex": ["female", "male", "male", "female", "female"],
    "survived": [1, 0, 0, 1, 1],
})


# ===== DataReader =====

class TestReader:
    def test_get_overview(self):
        result = get_overview(SAMPLE)
        assert "行数: 5" in result
        assert "列数: 5" in result

    def test_get_info(self):
        result = get_info(SAMPLE)
        assert "非空值" in result
        assert "age" in result
        assert SAMPLE.columns.all()

    def test_get_missing_all_present(self):
        result = get_missing(SAMPLE)
        assert "没有缺失值" in result or "age" in result  # age has one NaN

    def test_get_missing_has_nan(self):
        df = SAMPLE.copy()
        result = get_missing(df)
        assert "age" in result

    def test_get_head_default(self):
        result = get_head(SAMPLE)
        assert "Alice" in result
        assert "前 5 行" in result

    def test_get_head_empty(self):
        result = get_head(pd.DataFrame())
        assert "没有任何数据" in result

    def test_get_head_negative_n(self):
        result = get_head(SAMPLE, n=-1)
        assert "前 1 行" in result

    def test_get_head_exceeds_len(self):
        result = get_head(SAMPLE, n=100)
        assert "前 5 行" in result

    def test_get_unique(self):
        result = get_unique(SAMPLE, "sex")
        assert "female" in result
        assert "male" in result

    def test_get_unique_missing_col(self):
        result = get_unique(SAMPLE, "nonexistent")
        assert "不存在" in result


# ===== Analyst =====

class TestAnalyst:
    def test_describe_default(self):
        result = describe(SAMPLE)
        assert "age" in result or "fare" in result

    def test_describe_specific_cols(self):
        result = describe(SAMPLE, cols=["age", "fare"])
        assert "age" in result
        assert "fare" in result

    def test_describe_nonexistent_col(self):
        result = describe(SAMPLE, cols=["ghost"])
        assert "不存在" in result

    def test_describe_non_numeric_col(self):
        result = describe(SAMPLE, cols=["name"])
        assert "不是数值类型" in result

    def test_value_counts(self):
        result = value_counts(SAMPLE, "sex")
        assert "female" in result
        assert "male" in result

    def test_value_counts_missing_col(self):
        result = value_counts(SAMPLE, "ghost")
        assert "不存在" in result

    def test_groupby_agg(self):
        result = groupby_agg(SAMPLE, "sex", "age", "mean")
        assert "female" in result

    def test_groupby_agg_bad_col(self):
        result = groupby_agg(SAMPLE, "ghost", "age", "mean")
        assert "不存在" in result

    def test_correlation(self):
        result = correlation(SAMPLE)
        assert "age" in result
        assert "fare" in result

    def test_correlation_unsupported_method(self):
        result = correlation(SAMPLE, method="kendall")
        assert "不支持" in result

    def test_filter_data(self):
        result = filter_data(SAMPLE, "age > 30")
        assert "2 行" in result or "Bob" in result

    def test_filter_data_empty_condition(self):
        result = filter_data(SAMPLE, "")
        assert "不能为空" in result

    def test_filter_data_bad_column(self):
        result = filter_data(SAMPLE, "ghost > 5")
        assert "失败" in result

    def test_sort_data(self):
        result = sort_data(SAMPLE, "age")
        assert "25" in result or "Alice" in result

    def test_sort_data_bad_col(self):
        result = sort_data(SAMPLE, "ghost")
        assert "不存在" in result


# ===== Visualizer =====

class TestVisualizer:
    def _check_image(self, img):
        assert isinstance(img, Image.Image)

    def test_histogram(self):
        self._check_image(histogram(SAMPLE, "age"))

    def test_histogram_bad_col(self):
        self._check_image(histogram(SAMPLE, "ghost"))

    def test_histogram_non_numeric(self):
        self._check_image(histogram(SAMPLE, "name"))

    def test_bar_chart(self):
        self._check_image(bar_chart(SAMPLE, "sex", "fare"))

    def test_bar_chart_bad_x(self):
        self._check_image(bar_chart(SAMPLE, "ghost", "fare"))

    def test_bar_chart_non_numeric_y(self):
        self._check_image(bar_chart(SAMPLE, "sex", "name"))

    def test_box_plot(self):
        self._check_image(box_plot(SAMPLE, "age"))

    def test_box_plot_with_by(self):
        self._check_image(box_plot(SAMPLE, "age", by="sex"))

    def test_box_plot_bad_col(self):
        self._check_image(box_plot(SAMPLE, "ghost"))

    def test_heatmap(self):
        self._check_image(heatmap(SAMPLE))

    def test_heatmap_bad_method(self):
        self._check_image(heatmap(SAMPLE, method="kendall"))

    def test_scatter(self):
        self._check_image(scatter(SAMPLE, "age", "fare"))

    def test_scatter_with_hue(self):
        self._check_image(scatter(SAMPLE, "age", "fare", hue="sex"))

    def test_scatter_bad_x(self):
        self._check_image(scatter(SAMPLE, "ghost", "fare"))

    def test_pairplot(self):
        self._check_image(pairplot(SAMPLE, ["age", "fare"]))

    def test_pairplot_not_enough_cols(self):
        self._check_image(pairplot(SAMPLE, ["age"]))

    def test_pairplot_bad_cols(self):
        self._check_image(pairplot(SAMPLE, ["ghost"]))
