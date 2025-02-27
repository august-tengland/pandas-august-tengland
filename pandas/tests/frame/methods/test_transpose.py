import numpy as np
import pytest

import pandas.util._test_decorators as td

from pandas import (
    DataFrame,
    DatetimeIndex,
    IntervalIndex,
    Series,
    Timestamp,
    date_range,
    timedelta_range,
)
import pandas._testing as tm


class TestTranspose:
    def test_transpose_td64_intervals(self):
        # GH#44917
        tdi = timedelta_range("0 Days", "3 Days")
        ii = IntervalIndex.from_breaks(tdi)
        ii = ii.insert(-1, np.nan)
        df = DataFrame(ii)

        result = df.T
        expected = DataFrame({i: ii[i : i + 1] for i in range(len(ii))})
        tm.assert_frame_equal(result, expected)

    def test_transpose_empty_preserves_datetimeindex(self):
        # GH#41382
        df = DataFrame(index=DatetimeIndex([]))

        expected = DatetimeIndex([], dtype="datetime64[ns]", freq=None)

        result1 = df.T.sum().index
        result2 = df.sum(axis=1).index

        tm.assert_index_equal(result1, expected)
        tm.assert_index_equal(result2, expected)

    def test_transpose_tzaware_1col_single_tz(self):
        # GH#26825
        dti = date_range("2016-04-05 04:30", periods=3, tz="UTC")

        df = DataFrame(dti)
        assert (df.dtypes == dti.dtype).all()
        res = df.T
        assert (res.dtypes == dti.dtype).all()

    def test_transpose_tzaware_2col_single_tz(self):
        # GH#26825
        dti = date_range("2016-04-05 04:30", periods=3, tz="UTC")

        df3 = DataFrame({"A": dti, "B": dti})
        assert (df3.dtypes == dti.dtype).all()
        res3 = df3.T
        assert (res3.dtypes == dti.dtype).all()

    def test_transpose_tzaware_2col_mixed_tz(self):
        # GH#26825
        dti = date_range("2016-04-05 04:30", periods=3, tz="UTC")
        dti2 = dti.tz_convert("US/Pacific")

        df4 = DataFrame({"A": dti, "B": dti2})
        assert (df4.dtypes == [dti.dtype, dti2.dtype]).all()
        assert (df4.T.dtypes == object).all()
        tm.assert_frame_equal(df4.T.T, df4.astype(object))

    @pytest.mark.parametrize("tz", [None, "America/New_York"])
    def test_transpose_preserves_dtindex_equality_with_dst(self, tz):
        # GH#19970
        idx = date_range("20161101", "20161130", freq="4H", tz=tz)
        df = DataFrame({"a": range(len(idx)), "b": range(len(idx))}, index=idx)
        result = df.T == df.T
        expected = DataFrame(True, index=list("ab"), columns=idx)
        tm.assert_frame_equal(result, expected)

    def test_transpose_object_to_tzaware_mixed_tz(self):
        # GH#26825
        dti = date_range("2016-04-05 04:30", periods=3, tz="UTC")
        dti2 = dti.tz_convert("US/Pacific")

        # mixed all-tzaware dtypes
        df2 = DataFrame([dti, dti2])
        assert (df2.dtypes == object).all()
        res2 = df2.T
        assert (res2.dtypes == object).all()

    def test_transpose_uint64(self, uint64_frame):
        result = uint64_frame.T
        expected = DataFrame(uint64_frame.values.T)
        expected.index = ["A", "B"]
        tm.assert_frame_equal(result, expected)

    def test_transpose_float(self, float_frame):
        frame = float_frame
        dft = frame.T
        for idx, series in dft.items():
            for col, value in series.items():
                if np.isnan(value):
                    assert np.isnan(frame[col][idx])
                else:
                    assert value == frame[col][idx]

        # mixed type
        index, data = tm.getMixedTypeDict()
        mixed = DataFrame(data, index=index)

        mixed_T = mixed.T
        for col, s in mixed_T.items():
            assert s.dtype == np.object_

    @td.skip_array_manager_invalid_test
    def test_transpose_get_view(self, float_frame):
        dft = float_frame.T
        dft.values[:, 5:10] = 5

        assert (float_frame.values[5:10] == 5).all()

    @td.skip_array_manager_invalid_test
    def test_transpose_get_view_dt64tzget_view(self):
        dti = date_range("2016-01-01", periods=6, tz="US/Pacific")
        arr = dti._data.reshape(3, 2)
        df = DataFrame(arr)
        assert df._mgr.nblocks == 1

        result = df.T
        assert result._mgr.nblocks == 1

        rtrip = result._mgr.blocks[0].values
        assert np.shares_memory(arr._ndarray, rtrip._ndarray)

    def test_transpose_not_inferring_dt(self):
        # GH#51546
        df = DataFrame(
            {
                "a": [Timestamp("2019-12-31"), Timestamp("2019-12-31")],
            },
            dtype=object,
        )
        result = df.T
        expected = DataFrame(
            [[Timestamp("2019-12-31"), Timestamp("2019-12-31")]],
            columns=[0, 1],
            index=["a"],
            dtype=object,
        )
        tm.assert_frame_equal(result, expected)

    def test_transpose_not_inferring_dt_mixed_blocks(self):
        # GH#51546
        df = DataFrame(
            {
                "a": Series(
                    [Timestamp("2019-12-31"), Timestamp("2019-12-31")], dtype=object
                ),
                "b": [Timestamp("2019-12-31"), Timestamp("2019-12-31")],
            }
        )
        result = df.T
        expected = DataFrame(
            [
                [Timestamp("2019-12-31"), Timestamp("2019-12-31")],
                [Timestamp("2019-12-31"), Timestamp("2019-12-31")],
            ],
            columns=[0, 1],
            index=["a", "b"],
            dtype=object,
        )
        tm.assert_frame_equal(result, expected)
