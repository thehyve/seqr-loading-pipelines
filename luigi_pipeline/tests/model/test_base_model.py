import unittest

import hail as hl

from lib.model.base_mt_schema import BaseMTSchema, mt_annotation

class TestBaseModel(unittest.TestCase):

    def _test_schema_class(self):
        class TestSchema(BaseMTSchema):

            def __init__(self):
                super(TestSchema, self).__init__(hl.import_vcf('tests/data/1kg_30variants.vcf.bgz'))

            @mt_annotation()
            def a(self):
                return 0

            @mt_annotation(fn_require='a')
            def b(self):
                return self.mt.a + 1

            @mt_annotation(annotation='c', fn_require='a')
            def c_1(self):
                return self.mt.a + 2

        return TestSchema

    def test_schema_called_once_counts(self):
        test_schema = self._test_schema_class()()
        test_schema.a()
        fns = test_schema.all_annotation_fns()
        count_dict = {fn[0]: fn[1].mt_prop_meta['annotated'] for fn in fns}
        self.assertEqual(count_dict, {'a': 1, 'b': 0, 'c_1': 0})

    def test_schema_independent_counters(self):
        test_schema = self._test_schema_class()()
        test_schema.a()

        test_schema2 = self._test_schema_class()()
        test_schema2.b()

        fns = test_schema.all_annotation_fns()
        count_dict = {fn[0]: fn[1].mt_prop_meta['annotated'] for fn in fns}
        self.assertEqual(count_dict, {'a': 1, 'b': 0, 'c_1': 0})

    def test_schema_dependencies(self):
        test_schema = self._test_schema_class()()
        test_schema.b()

        fns = test_schema.all_annotation_fns()
        count_dict = {fn[0]: fn[1].mt_prop_meta['annotated'] for fn in fns}
        self.assertEqual(count_dict, {'a': 1, 'b': 1, 'c_1': 0})

    def test_schema_called_at_most_once(self):
        test_schema = self._test_schema_class()()
        test_schema.a().b().c_1()

        fns = test_schema.all_annotation_fns()
        count_dict = {fn[0]: fn[1].mt_prop_meta['annotated'] for fn in fns}
        self.assertEqual(count_dict, {'a': 1, 'b': 1, 'c_1': 1})

    def test_schema_annotate_all(self):
        test_schema = self._test_schema_class()()
        test_schema.a().annotate_all()

        fns = test_schema.all_annotation_fns()
        count_dict = {fn[0]: fn[1].mt_prop_meta['annotated'] for fn in fns}
        self.assertEqual(count_dict, {'a': 1, 'b': 1, 'c_1': 1})

    def test_schema_mt_select_annotated_mt(self):
        test_schema = self._test_schema_class()()
        mt = test_schema.a().annotate_all().select_annotated_mt()
        first_row = mt.rows().take(1)[0]

        self.assertEqual(first_row.a, 0)
        self.assertEqual(first_row.b, 1)
        self.assertEqual(first_row.c, 2)
