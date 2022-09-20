export const getCurrentWord = (text, pos) => {
  const firstPart = text.slice(0, pos).split(/\s|\n/);
  const lastPart = text.slice(pos).split(/\s|\n/);
  const firstPiece = firstPart[firstPart.length - 1];
  const lastPiece = lastPart[0];

  const from = pos - firstPiece.length;
  const to = pos + lastPiece.length;

  return { word: `${firstPiece}${lastPiece}`, from, to };
};
