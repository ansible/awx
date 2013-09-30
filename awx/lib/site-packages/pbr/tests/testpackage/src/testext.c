#include <Python.h>


static PyMethodDef TestextMethods[] = {
    {NULL, NULL, 0, NULL}
};


#if PY_MAJOR_VERSION >=3
static struct PyModuleDef testextmodule = {
    PyModuleDef_HEAD_INIT,
    "testext",
    -1,
    TestextMethods
};

PyObject*
PyInit_testext(void)
{
    return PyModule_Create(&testextmodule);
}
#else
PyMODINIT_FUNC
inittestext(void)
{
    Py_InitModule("testext", TestextMethods);
}
#endif
