| Format           |     288 |         3652 |    104999 | Precision        | Clarity       |
|------------------|--------:|-------------:|----------:|------------------|---------------|
| str(_)[:3]       |     288 |       365... |    104... | Lots too little  | Cut too short |
| ls -lh           |    288B |         3.6K |      103K | Still too little | Fuzzy         |
| ls -l            | **288** |         3652 |    104999 | Too much         | Fuzzy         |
| {:.2f}           |  288.00 |      3652.00 | 104999.00 | Much too much    | Fuzzy         |
| round(_/1000, 2) |   0.29k |    **3.65k** |    105.0k | Sometimes great  | Fuzzy         |
| {:.3g}           | **288** | **3.65e+03** |  1.05e+05 | More often great | Fuzzy         |
| eng              | **288** |   **3.65e3** | **104e3** | **Just Enough**  | **Clear**     |
