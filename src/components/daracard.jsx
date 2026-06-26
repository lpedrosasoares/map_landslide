const DataCard = (props) => {
  return (
    <div
      onClick={props.onClick}
      className="m-5 p-5 flex items-center justify-between border rounded-2xl bg-amber-100 shadow-sm hover:bg-green-200 transition-all duration-200 cursor-pointer"
    >
      <div className="flex flex-col">
        <p className="text-2xl font-semibold text-gray-800">{props.location}</p>
        <p className="text-lg text-gray-600">{props.authors}</p>
      </div>

      <span className="px-3 py-1 text-lg font-bold bg-amber-300 text-black rounded-full shadow-sm">
        {props.year}
      </span>
    </div>
  );
};

export default DataCard;
