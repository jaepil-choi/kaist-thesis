import csv

def process_csv(input_file, add_file, output_file):
    with open(output_file, 'w') as tex_file:
        tex_file.write(r'\newcommand{\department}[3]{%'+'\n')

        with open(input_file, 'r', newline='') as csv_input:
            reader = csv.reader(csv_input)
            next(reader)

            for row in reader:
                """
                row[0]: Department Code
                row[1]: childDeptNameKor
                row[2]: childDeptNameEng
                row[3]: parentDeptNameKor
                row[4]: parentDeptNameEng
                row[5]: parentAcademNameEng
                row[6]: childAcademNameEng

                Example Code Snippet:
                \ifthenelse{\equal{#1}{PH}}
                    {\renewcommand{\@degreeCode}{\@degreePrefix #1}
                    \renewcommand{\@childDeptNameKor}{물리학과}
                    \renewcommand{\@childDeptNameEng}{Department of Physics}
                    \renewcommand{\@parentDeptNameKor}{}
                    \renewcommand{\@parentDeptNameEng}{}
                    \renewcommand{\@parentAcademNameEng}{}
                    \renewcommand{\@childAcademNameEng}{Physics}
                    \renewcommand{\@degreeField}{#2}
                    \renewcommand{\@degreeversion}{#3}}{}
                """
                tex_file.write('\t'+r'\ifthenelse{\equal{#1}{'+row[0]+r'}}'+'\n')
                tex_file.write('\t\t'+r'{\renewcommand{\@degreeCode}{\@degreePrefix #1}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@childDeptNameKor}{'+row[1]+r'}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@childDeptNameEng}{'+row[2]+r'}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@parentDeptNameKor}{'+row[3]+r'}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@parentDeptNameEng}{'+row[4]+r'}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@parentAcademNameEng}{'+row[5]+r'}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@childAcademNameEng}{'+row[6]+r'}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@degreeField}{#2}'+'\n')
                tex_file.write('\t\t'+r'\renewcommand{\@degreeversion}{#3}}{}'+'\n')


        tex_file.write('\n')
        with open(add_file, 'r', newline='') as add_input:
            content = add_input.read()
            tex_file.write(content)
        tex_file.write('\n')

        tex_file.write(r'}'+'\n')
        tex_file.write(r'\@onlypreamble{\department}')
    
    print(f"Processed .csv file, saved TeX code to {output_file}")


if __name__ == "__main__":
    # Example usage:
    input_file = 'department_names.csv'
    add_file = 'additional.txt'
    output_file = 'department_names.tex'
    process_csv(input_file, add_file, output_file)