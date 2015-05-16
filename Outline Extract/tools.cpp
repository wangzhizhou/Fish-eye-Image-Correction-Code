#include "tools.h"

string tools::filePathToProcess = "";
Mat tools::image = Mat();

void tools::DisplayImage(Mat img)
{

}

Mat tools::GetImage()
{
	if (image.data)
		return image;
}

bool tools::readImage()
{
	if (GetFilePathToProcess())
	{
		image = imread(tools::filePathToProcess, IMREAD_COLOR);
		
		if (!image.data)
		{
			Tip("Failed to read in a image.");
			Tip("");
			return false;
		}
		return true;
	}
	else
	{

		Tip("You should select an image to process in the dialog!");
		Tip("");
	}
	return false;
}
bool tools::GetFilePathToProcess()
{
	OPENFILENAME ofn;
	char szFile[MAX_PATH];
	ZeroMemory(&ofn, sizeof(ofn));
	ofn.lStructSize = sizeof(ofn);
	ofn.lpstrFile = szFile;
	ofn.lpstrFile[0] = TEXT('\0');
	ofn.nMaxFile = sizeof(szFile);
	ofn.lpstrFilter = TEXT("jpg\0*.jpg\0bmp\0*.bmp\0png\0*.png\0"); //定义三个选项 jpg/bmp/png图片格式
	ofn.nFilterIndex = 1;      //定义首选项是哪一个
	ofn.lpstrFileTitle = NULL;
	ofn.nMaxFileTitle = 0;
	ofn.lpstrInitialDir = NULL;
	ofn.Flags = OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
	if (GetOpenFileName(&ofn))
	{	
		filePathToProcess = szFile;
#ifdef _DEBUG
		cout << "The path of image to be opened is:"<<endl
			<<"\t"<<filePathToProcess << endl;
#endif // _DEBUG	
		return true;
	}
	return false;
}

//用法提示
void tools::Tip(string message)
{
	if (message.empty())
	{
		cout << "Press \"Enter\" to exit ...";
		getchar();
		exit(0);
	}
	else
	{
		cout << "******* MESSAGE *******"<<endl
			<<message << endl 
			<< "***********************"<<endl;
	}
}