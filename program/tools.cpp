#include "tools.h"

vector<string> tools::fileNames;
vector<Mat> tools::images;

vector<Mat>& tools::GetImages()
{
	if (images.size())
		return images;

	images = vector<Mat>();
	return images;
}

bool tools::readImage(vector<string> imagePaths)
{
	fileNames = imagePaths;
	if (!fileNames.empty())
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