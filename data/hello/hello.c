#include "hello.h"

void bar()
{
}

void foo()
{
    bar();
    buz();
}

void buz() {}

void hi()
{
    foo();
}

void hello()
{
    bar();
    hi();
}
