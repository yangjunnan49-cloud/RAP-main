from pathlib import Path
import argparse
import pypdfium2 as pdfium
ap=argparse.ArgumentParser();ap.add_argument('pdf');ap.add_argument('out');ap.add_argument('--scale',type=float,default=1.5);args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
pdf=pdfium.PdfDocument(args.pdf)
for i in range(len(pdf)):
    page=pdf[i];page.render(scale=args.scale).to_pil().convert('RGB').save(out/f'page-{i+1:02d}.png');page.close()
print(f'{len(pdf)} pages rendered to {out}')
pdf.close()
