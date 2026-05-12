#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("This function creates a list.")

def makelist():
    a = []
    for i in range(1, 20):
        a.append(i)
        print("appending", i, ":", a)
        return a

if __name__ == "__main__":
    makelist()