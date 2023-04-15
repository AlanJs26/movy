# Introduction

This command line app allows users to move and rename files using a custom scripting language. The app provides a powerful and efficient way to automate file organization tasks, saving users time and effort.

The app allows users to create and execute custom scripts that specify the files to move and rename, as well as the target directories and new file names. With a simple and intuitive syntax, users can quickly and easily perform complex file management tasks with just a few lines of code.

# Features

Here are some of the key features of the app:

Custom scripting language: The app provides a simple and powerful scripting language that allows users to specify exactly which files to move and rename, and where to move them to.

- File selection: Users can select files based on various criteria, such as file type, name pattern, size, and date modified.

- File renaming: Users can rename files using a variety of patterns and variables, such as the current date, file size, and file type.

- Target directories: Users can specify the target directories where they want to move their files to, and create new directories as needed.

- Preview mode: The app includes a preview mode that allows users to see the changes that will be made before actually executing the script, giving them the chance to make any necessary adjustments.


# Installing

You can install movy using pip:

```bash
pip install movy
```

Now run `movy --help` to test if the program works.

# Getting Started

All scripts are located in `~/.movy/scripts/` and each script is run in a single folder, specified by the `root`. In the example below the root is `~/Downloads`

```movy
---
root: ~/Downloads
---

[[Text Files]]
extension: txt,md
move -> ~/Documents/

[[School Stuff]]
filecontent: /school/i
move -> ~/Documents/School
```

In this example, the first block selects all files with `.txt` or `.md` extension and moves them to the `~/Documents` directory. The `~` symbol represents the home directory of the current user.

The second block selects all files that have the word "school" in their name, using a regular expression `/school/i`, and moves them to `~/Documents/School`.

You can modify this script to suit your specific file organization needs, using the custom scripting language provided by the app.

# Rules

Rules are written as `rule_name: content` and has the function to filter incoming files based on specific criteria. The available rules are listed below

## basename

this rule compare only the basename of the file (excluding the extension) with the content field. It accepts a unix glob or a regexp.

```
├── algorithms
│  ├── binarySearch.cpp
│  ├── insertionSort.cpp
│  ├── linearSearch.cpp
│  ├── mergeSort.cpp
│  ├── quickSort.cpp
│  └── selectionSort.cpp
├── Hashmap.cpp
├── Hashmap.h
├── HashmapChained.cpp
├── HashmapChained.h
├── Heap.cpp
├── Heap.h
├── Item.cpp
├── Item.h
├── Linkedlist.cpp
├── Linkedlist.h
├── List.cpp
├── List.h
├── main.cpp
├── main.exe
├── Makefile
├── Queue.cpp
├── Queue.h
└── testDataStructures.cpp

```
```movy
[[Basename Example]]
basename: List
move -> path/to/file
```

Given the file structure and the snippet listed above, this code will move all files that have the basename equals to "List" (List.cpp and List.h)

if instead of `List` as the pattern was written `Li*`, the selected files would be Linkedlist.cpp, Linkedlist.h, List.cpp and List.h


## extension

This rule extract only the extension of the file and compares it to a glob or regexp

```movy
[[Extension Example]]
extension: cpp
move -> path/to/file
```

Using the same file structure as before, this script moves all files with the `.cpp` extension. That files being: Hashmap.cpp, Heap.cpp, Linkedlist.cpp, main.cpp, Queue.cpp, HashmapChained.cpp, Item.cpp, List.cpp, PriorityList.cpp and testDataStructures.cpp

## file

This rule compares the whole path to the content field.
Using the previous examples, if the full path to that folder were `~/Documents/Codes/CPP/DataStructures` a rule:

```movy
[[File Example]]
file: /CPP/
move -> path/to/file
```

would match all of them. 

> In this example `/CPP/` is a regexp that matches CPP (case sensitive) everywhere in the string

## pdf_template

This rule use a template pdf file to compare other similar looking pdfs.

```movy
[[Pdf Template Example]]
pdf_template: {
    base_file: ~/Documents/Templates/water_bill.pdf
    score: 70
}
move -> path/to/file
```

In the snippet above, the rule will match all files that are visually similar. It will compare only the first page and the `score` arguments can be adjusted to fine tune how much similar do you want the matched documents be


## hasproperty

As files are going from rule to rule they can be assigned properties, such as regexp group contents and others


```movy
[[Has Property Example]]
basename: *rc
not hasproperty: is_syslink
move -> ~/Documents/dotfiles_backup
syslink -> 
```

This snippet:
- selects all files the ends with "rc" (such as bashrc or zshrc)
- checks if the file not has the property "is_syslink"
- move it to a backup folder
- syslink it back to the current folder

## filecontent

This rule compare a file contents to a glob or regexp.

```movy
[[Filecontent Example]]
basename: /water/i
filecontent: /Customer: *(?P<name>[a-zA-Z]+)/
move -> ~/Documents/{name}/water_bills
```

The example above first select all files that contains water in their basename, then executes a regexp that find the customer name, finally, move this this file to the folder water_bills inside a folder with the same name as the found by the regexp

# Actions

Actions are written as `action_name -> content` and has the function to act upon the incoming files modifying it or making changes to the file structure . The available actions are listed below

## echo

This action simply echoes the file name or a message to the screen.

```movy
[[Echo Example]]
basename: /water/i
echo ->
```

The output of the example above will be:

```
Echo: ~/Downloads/water bill 1.pdf
Echo: ~/Downloads/program.exe
Echo: ~/Downloads/some_file.txt
```

Is also possible use expressions in the content field to extract useful information of the file

```movy
[[Echo Example]]
basename: /water/i
echo -> {extension}
```

Output:

```
pdf
exe
txt
```

## move

This rule move files. Writing `makedirs` as argument will create all missing directories to the requested output path

## trash

This rule delete files. Using `confirm` as argument will create a confirmation prompt before every deletion


