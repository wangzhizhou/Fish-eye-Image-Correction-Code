#include "tools.h"

vector<string> tools::fileNames;
vector<Mat> tools::images;

vector<Mat>& tools::GetImages()
{
	if (images.size())
		return images;
	return vector<Mat>();
}

bool tools::readImage()
{
	cout << "Select Image File(s): " << endl<<endl;
	if (GetFilePathToProcess())
	{
		images.clear();
		for (int i = 0;i < fileNames.size();i++)
		{
			Mat image = cv::imread(fileNames[i], cv::IMREAD_COLOR);
			if (image.empty())
			{
				Tip("Failed to read in a image.");
				Tip("");
				return false;
			}
			cout <<"\t"<<fileNames[i] << endl;
			images.push_back(image);
		}
		cout << endl << "Read " << fileNames.size() << " files" << endl << endl;
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

	CHAR szOpenFileNames[80 * MAX_PATH];
	TCHAR szPath[MAX_PATH];
	TCHAR szFileName[MAX_PATH];
	TCHAR* p;
	int nLen = 0;

	char curPath[MAX_PATH];
	GetCurrentDirectory(MAX_PATH, curPath);

	ZeroMemory(&ofn, sizeof(ofn));
	ofn.lStructSize = sizeof(ofn);
	ofn.lpstrFile = szOpenFileNames;
	ofn.lpstrFile[0] = TEXT('\0');
	ofn.nMaxFile = sizeof(szOpenFileNames);
	ofn.lpstrFilter = TEXT("jpg\0*.jpg\0bmp\0*.bmp\0png\0*.png\0"); //定义三个选项 jpg/bmp/png图片格式
	ofn.nFilterIndex = 1;      //定义首选项是哪一个
	ofn.lpstrFileTitle = NULL;
	ofn.nMaxFileTitle = 0;
	ofn.lpstrInitialDir = NULL;
	ofn.Flags = OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST|OFN_ALLOWMULTISELECT;
	ofn.lpstrInitialDir = curPath;

	if (GetOpenFileName(&ofn))
	{	
		lstrcpyn(szPath, szOpenFileNames, ofn.nFileOffset);
		szPath[ofn.nFileOffset] = '\0';
		nLen = lstrlen(szPath);

		if (szPath[nLen - 1] != '\\')   //如果选了多个文件,则必须加上'\\'
		{
			lstrcat(szPath, TEXT("\\"));
		}

		p = szOpenFileNames + ofn.nFileOffset; //把指针移到第一个文件

		ZeroMemory(szFileName, sizeof(szFileName));
		while (*p)
		{
			lstrcpy(szFileName, szPath);  //给文件名加上路径  
			lstrcat(szFileName, p);    //加上文件名   
			fileNames.push_back(string(szFileName));
			p += lstrlen(p) + 1;     //移至下一个文件
		}

#ifdef _DEBUG
		cout << "The path of image to be opened is:" << endl;
		for (int i = 0;i < fileNames.size();i++)
			cout << fileNames[i] << endl;
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